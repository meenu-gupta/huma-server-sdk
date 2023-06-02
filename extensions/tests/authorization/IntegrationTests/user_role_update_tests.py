from unittest.mock import MagicMock

from bson import ObjectId

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.router.user_profile_request import (
    AddRolesToUsersRequestObject,
    UpdateUserRoleRequestObject,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import Client
from .test_helpers import (
    MANAGER_1_ID_DEPLOYMENT_X,
    MANAGER_2_ID_DEPLOYMENT_Y,
    DEPLOYMENT_2_ID,
    ACCESS_CONTROLLER_ID,
    ORGANIZATION_ID,
    ORGANIZATION_STAFF_ID,
    CALL_CENTER_ID,
    DEPLOYMENT_STAFF_ID,
    MANAGER_2_ID_DEPLOYMENT_X,
    DEPLOYMENT_ID,
    CONTRIBUTOR_1_ID_DEPLOYMENT_X,
    CUSTOM_ROLE_1_ID_DEPLOYMENT_X,
    SUPER_ADMIN_ID,
    HUMA_SUPPORT_ID,
    ORGANIZATION_ADMINISTRATOR_ID,
    DEPLOYMENT_ADMINISTRATOR_ID,
    SUPPORT_ID,
    ORG_EDITOR_ID,
    ORG_OWNER_ID,
    SUPERVISOR_ID,
)
from .user_router_tests import BaseCRUDPermissionTestCase

ORG_ROLE_USER_IDS = {
    RoleName.ACCESS_CONTROLLER: ACCESS_CONTROLLER_ID,
    RoleName.ORGANIZATION_OWNER: ORG_OWNER_ID,
    RoleName.ORGANIZATION_EDITOR: ORG_EDITOR_ID,
    RoleName.ORGANIZATION_STAFF: ORGANIZATION_STAFF_ID,
    RoleName.SUPPORT: SUPPORT_ID,
    RoleName.ADMINISTRATOR: ORGANIZATION_ADMINISTRATOR_ID,
    RoleName.SUPERVISOR: SUPERVISOR_ID,
}
DEPLOYMENT_ROLE_USER_IDS = {
    RoleName.ADMIN: MANAGER_1_ID_DEPLOYMENT_X,
    RoleName.CALL_CENTER: CALL_CENTER_ID,
    RoleName.DEPLOYMENT_STAFF: DEPLOYMENT_STAFF_ID,
}


class MockEmailAdapter:
    instance = MagicMock()
    send_assign_new_roles_email = MagicMock()
    send_assign_new_multi_resource_role = MagicMock()


class OldUserRoleUpdateTestCase(BaseCRUDPermissionTestCase):
    """@deprecated"""

    def setUp(self):
        def bind_adapters(binder):
            binder.bind_to_provider(EmailInvitationAdapter, lambda: MockEmailAdapter())

        super(OldUserRoleUpdateTestCase, self).setUp()
        inject.get_injector_or_die().rebind(config=bind_adapters)
        MockEmailAdapter.send_assign_new_roles_email.reset_mock()

    def get_user_from_db(self, user_id):
        return self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})

    def assign_roles(self, json):
        return self.flask_client.post(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/assign-roles",
            json=json,
            headers=self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X),
        )

    def test_success_add_roles(self):
        role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
        rsp = self.assign_roles({UpdateUserRoleRequestObject.ROLES: [role.to_dict()]})
        self.assertEqual(200, rsp.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(1, len(user[User.ROLES]))
        role.userType = Role.UserType.MANAGER
        self.assertIn(role.to_dict(), user[User.ROLES])

    def test_success_remove_role(self):
        rsp = self.assign_roles({UpdateUserRoleRequestObject.ROLES: []})
        self.assertEqual(200, rsp.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(0, len(user[User.ROLES]))


class UserRoleUpdateTestCase(BaseCRUDPermissionTestCase):
    def setUp(self):
        def bind_adapters(binder):
            binder.bind_to_provider(EmailInvitationAdapter, lambda: MockEmailAdapter())

        super(UserRoleUpdateTestCase, self).setUp()
        inject.get_injector_or_die().rebind(config=bind_adapters)
        MockEmailAdapter.send_assign_new_roles_email.reset_mock()
        MockEmailAdapter.send_assign_new_multi_resource_role.reset_mock()

    def get_user_from_db(self, user_id):
        return self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})

    def add_roles(
        self,
        json,
        manager_id=MANAGER_2_ID_DEPLOYMENT_X,
        target_id=MANAGER_1_ID_DEPLOYMENT_X,
    ):
        return self.flask_client.post(
            f"{self.base_path}/{target_id}/add-role",
            json=json,
            headers=self.get_headers_for_token(manager_id),
        )

    def test_success_add_roles(self):
        role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(200, rsp.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(1, len(user[User.ROLES]))
        self.assertIn(role.to_dict(), user[User.ROLES])

    def test_failure_add_role(self):
        roles = [{"resource": "Test", "roleId": "Admin"}]
        rsp = self.add_roles(roles)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100050, rsp.json["code"])

    def test_success_remove_role(self):
        manager_headers = self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X)
        role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        rsp = self.flask_client.post(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/remove-role",
            json=[role.to_dict()],
            headers=manager_headers,
        )
        self.assertEqual(204, rsp.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(0, len(user[User.ROLES]))

    def test_success_add_existing_role(self):
        role: RoleAssignment = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(200, rsp.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(1, len(user[User.ROLES]))

    def test_failure_remove_missing_role(self):
        role: RoleAssignment = RoleAssignment.create_role(
            RoleName.CONTRIBUTOR, DEPLOYMENT_ID
        )
        rsp = self.flask_client.post(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/remove-role",
            json=[role.to_dict()],
            headers=self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_update_org_staff_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], ACCESS_CONTROLLER_ID, ORGANIZATION_STAFF_ID
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_update_user_roles_dif_target_deployment(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_update_user_roles_dif_users_deployment(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        routes = ["add-role", "remove-role"]
        headers = self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X)
        for route in routes:
            rsp = self.flask_client.post(
                f"{self.base_path}/{MANAGER_2_ID_DEPLOYMENT_Y}/{route}",
                json=[role.to_dict()],
                headers=headers,
            )
            self.assertEqual(403, rsp.status_code, route)

    def test_failure_update_user_roles_by_contributor(self):
        routes = ["add-role", "remove-role"]
        headers = self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X)
        for route in routes:
            rsp = self.flask_client.post(
                f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/{route}",
                json=[],
                headers=headers,
            )
            self.assertEqual(403, rsp.status_code, route)

    def test_failure_update_user_roles_to_patient_user(self):
        role = RoleAssignment.create_role(RoleName.USER, "5d386cc6ff885918d96edb44")
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_user_roles_to_super_admin(self):
        role = RoleAssignment.create_role(
            RoleName.SUPER_ADMIN, "5d386cc6ff885918d96edb44"
        )
        rsp = self.add_roles(
            [role.to_dict()], CONTRIBUTOR_1_ID_DEPLOYMENT_X, MANAGER_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_user_roles_when_invalid_role_provided(self):
        role = {
            "roleId": "InvalidRole",
            "resource": f"deployment/{DEPLOYMENT_ID}",
        }
        rsp = self.flask_client.post(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/add-role",
            json=[role],
            headers=self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_user_roles_by_custom_role(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        rsp = self.flask_client.post(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/add-role",
            json=[role.to_dict()],
            headers=self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_update_user_organization_role_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        rsp = self.add_roles(
            [role.to_dict()], ACCESS_CONTROLLER_ID, ORGANIZATION_STAFF_ID
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_remove_organization_role_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        rsp = self.flask_client.post(
            f"{self.base_path}/{ORGANIZATION_STAFF_ID}/remove-role",
            json=[role.to_dict()],
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        self.assertEqual(204, rsp.status_code)

    def test_failure_update_user_deployment_role_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        routes = ["add-role", "remove-role"]
        for route in routes:
            rsp = self.flask_client.post(
                f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/{route}",
                json=[role.to_dict()],
                headers={
                    **self.get_headers_for_token(ACCESS_CONTROLLER_ID),
                    "x-org-id": ORGANIZATION_ID,
                },
            )
            self.assertEqual(400, rsp.status_code)

    def test_failure_update_user_organization_role_by_admin(self):
        role = RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_user_deployment_staff_by_admin(self):
        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(400, rsp.status_code)

    def test_success_update_user_deployment_custom_role_to_deployment_staff_by_access_controller(
        self,
    ):
        access_controller_id = "5ed803dd5f2f99da73654410"
        org_customrole_user = "6070b68c698f355159e1b724"

        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], access_controller_id, org_customrole_user
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_update_user_deployment_custom_role_to_deployment_staff_by_org_custom_role(
        self,
    ):
        org_customrole_user_submitter = "61920aa2b39e8acfb70a761c"
        org_customrole_user = "6070b68c698f355159e1b724"

        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], org_customrole_user_submitter, org_customrole_user
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_update_admin_by_super_admin(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], SUPER_ADMIN_ID, CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_update_admin_by_huma_support(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], HUMA_SUPPORT_ID, CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_update_new_roles_by_org_administrator(self):
        role = RoleAssignment.create_role("6151051575fee50d15298adb", ORGANIZATION_ID)
        test_users = [SUPPORT_ID, SUPERVISOR_ID, DEPLOYMENT_ADMINISTRATOR_ID]
        for user in test_users:
            rsp = self.add_roles([role.to_dict()], ORGANIZATION_ADMINISTRATOR_ID, user)
            self.assertEqual(200, rsp.status_code)

    def test_success_update_custom_roles_by_org_administrator(self):
        role = RoleAssignment.create_role(
            RoleName.ADMINISTRATOR, ORGANIZATION_ID, "organization"
        )
        test_users = ["61920aa2b39e8acfb70a761c"]
        for user in test_users:
            rsp = self.add_roles([role.to_dict()], ORGANIZATION_ADMINISTRATOR_ID, user)
            self.assertEqual(200, rsp.status_code)

    def test_success_update_custom_roles_by_dep_administrator(self):
        role = RoleAssignment.create_role(
            RoleName.ADMINISTRATOR, DEPLOYMENT_ID, "deployment"
        )
        test_users = ["600720843111683010a73b4e"]
        for user in test_users:
            rsp = self.add_roles([role.to_dict()], DEPLOYMENT_ADMINISTRATOR_ID, user)
            self.assertEqual(200, rsp.status_code)

    def test_success_update_new_roles_by_dep_administrator(self):
        role = RoleAssignment.create_role("5e8eeae1b707216625ca4203", DEPLOYMENT_ID)
        rsp = self.add_roles(
            [role.to_dict()], DEPLOYMENT_ADMINISTRATOR_ID, DEPLOYMENT_ADMINISTRATOR_ID
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_deployment_add_role_custom_role(self):
        custom_role_id = "5e8eeae1b707216625ca4203"
        deployment_id = "5d386cc6ff885918d96edb2c"

        role = RoleAssignment.create_role(custom_role_id, deployment_id)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(MANAGER_1_ID_DEPLOYMENT_X, rsp.json["id"])

        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_roles_email.assert_called_once_with(
            "manager@manager.com",
            client,
            "en",
            "manager2 manager2",
            "Custom Role",
            "Admin",
        )

    def test_success_add_org_role_by_org_administrator(self):
        # Org role - Org level
        roles_to_test = [RoleName.ADMINISTRATOR, RoleName.SUPPORT]
        for test_role in roles_to_test:
            role = RoleAssignment.create_role(
                test_role, ORGANIZATION_ID, "organization"
            )
            rsp = self.add_roles(
                [role.to_dict()],
                ORGANIZATION_ADMINISTRATOR_ID,
                ORG_ROLE_USER_IDS.get(test_role),
            )
            self.assertEqual(200, rsp.status_code)

    def test_success_add_dep_role_by_org_administrator(self):
        # Org role - Deployment level
        role = RoleAssignment.create_role(RoleName.SUPPORT, DEPLOYMENT_ID, "deployment")
        rsp = self.add_roles(
            [role.to_dict()], ORGANIZATION_ADMINISTRATOR_ID, DEPLOYMENT_ADMINISTRATOR_ID
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_add_dep_role_by_dep_administrator(self):
        # Deployment role - Deployment level
        role = RoleAssignment.create_role(RoleName.SUPPORT, DEPLOYMENT_ID, "deployment")
        rsp = self.add_roles(
            [role.to_dict()], DEPLOYMENT_ADMINISTRATOR_ID, DEPLOYMENT_ADMINISTRATOR_ID
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_add_org_role_by_dep_administrator(self):
        # Org role - Deployment level
        role = RoleAssignment.create_role(
            RoleName.SUPPORT, ORGANIZATION_ID, "deployment"
        )
        rsp = self.add_roles(
            [role.to_dict()], DEPLOYMENT_ADMINISTRATOR_ID, ORGANIZATION_ADMINISTRATOR_ID
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_add_old_roles_by_org_administrator(self):
        roles_to_test = [
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
            RoleName.ORGANIZATION_EDITOR,
            RoleName.ORGANIZATION_OWNER,
        ]
        for test_role in roles_to_test:
            role = RoleAssignment.create_role(test_role, ORGANIZATION_ID)
            rsp = self.add_roles(
                [role.to_dict()],
                ORGANIZATION_ADMINISTRATOR_ID,
                ORG_ROLE_USER_IDS.get(test_role),
            )
            self.assertEqual(400, rsp.status_code)

    def test_failure_add_old_roles_by_dep_administrator(self):
        roles_to_test = [
            RoleName.ADMIN,
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
        ]
        for test_role in roles_to_test:
            role = RoleAssignment.create_role(test_role, DEPLOYMENT_ID)
            rsp = self.add_roles(
                [role.to_dict()],
                DEPLOYMENT_ADMINISTRATOR_ID,
                DEPLOYMENT_ROLE_USER_IDS.get(test_role),
            )
            self.assertEqual(400, rsp.status_code)

    def test_success_organization_add_custom_role(self):
        custom_role_id = "6151051575fee50d15298adb"
        organization_id = "5fde855f12db509a2785da06"
        access_controller_id = "5ed803dd5f2f99da73654410"
        other_user = "6156477be8a969c484d4cbed"

        role = RoleAssignment.create_role(custom_role_id, organization_id)
        rsp = self.add_roles([role.to_dict()], access_controller_id, other_user)
        self.assertEqual(200, rsp.status_code)

        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_roles_email.assert_called_once_with(
            "access+1@controller.com",
            client,
            "en",
            "Access Controller",
            "Custom org role",
            "Access Controller",
        )

    def test_success_remove_role_org_administrator(self):
        roles_to_test = [RoleName.SUPPORT]
        for test_role in roles_to_test:
            role = RoleAssignment.create_role(test_role, ORGANIZATION_ID)
            rsp = self.flask_client.post(
                f"{self.base_path}/{ORG_ROLE_USER_IDS.get(test_role)}/remove-role",
                json=[role.to_dict()],
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(204, rsp.status_code)
            user = self.get_user_from_db(ORG_ROLE_USER_IDS.get(test_role))
            self.assertEqual(0, len(user[User.ROLES]))

    def test_failure_remove_role_org_administrator(self):
        roles_to_test = [
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
            RoleName.ORGANIZATION_EDITOR,
            RoleName.ORGANIZATION_OWNER,
        ]
        for test_role in roles_to_test:
            role = RoleAssignment.create_role(test_role, ORGANIZATION_ID)
            rsp = self.flask_client.post(
                f"{self.base_path}/{ORG_ROLE_USER_IDS.get(test_role)}/remove-role",
                json=[role.to_dict()],
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(400, rsp.status_code)

    def test_success_organization_add_custom_role_by_org_administrator(self):
        custom_role_id = "6151051575fee50d15298adb"

        role = RoleAssignment.create_role(custom_role_id, ORGANIZATION_ID)
        rsp = self.add_roles(
            [role.to_dict()], ORGANIZATION_ADMINISTRATOR_ID, SUPPORT_ID
        )
        self.assertEqual(200, rsp.status_code)

        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_roles_email.assert_called_once_with(
            "support@org.com",
            client,
            "en",
            "Administrator Org",
            "Custom org role",
            "Support",
        )

    def test_success_send_email_notification(self):
        role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
        rsp = self.add_roles([role.to_dict()])
        self.assertEqual(200, rsp.status_code)
        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_roles_email.assert_called_once_with(
            "manager@manager.com",
            client,
            "en",
            "manager2 manager2",
            "Contributor",
            "Admin",
        )

    def test_success_send_email_notification_multi_resource_deployment_staff(self):
        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_2_ID)
        rsp = self.add_roles(
            [role.to_dict()], ACCESS_CONTROLLER_ID, DEPLOYMENT_STAFF_ID
        )
        self.assertEqual(200, rsp.status_code)
        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_multi_resource_role.assert_called_once_with(
            "deployment@staff.com",
            client,
            "en",
            "Access Controller",
            "Deployment Staff",
            "Y",
        )

    def test_success_send_email_notification_multi_resource_call_center(self):
        role = RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID)
        rsp = self.add_roles([role.to_dict()], ACCESS_CONTROLLER_ID, CALL_CENTER_ID)
        self.assertEqual(200, rsp.status_code)
        project = self.config.server.project
        client = project.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
        MockEmailAdapter.send_assign_new_multi_resource_role.assert_called_once_with(
            "call1@center.com",
            client,
            "en",
            "Access Controller",
            "Patient support",
            "Y",
        )


class AddRolesToUsersTestCase(BaseCRUDPermissionTestCase):
    def setUp(self):
        def bind_adapters(binder):
            binder.bind_to_provider(EmailInvitationAdapter, lambda: MockEmailAdapter())

        super(AddRolesToUsersTestCase, self).setUp()
        inject.get_injector_or_die().rebind(config=bind_adapters)
        MockEmailAdapter.send_assign_new_roles_email.reset_mock()
        MockEmailAdapter.send_assign_new_multi_resource_role.reset_mock()

    def get_user_from_db(self, user_id):
        return self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})

    def add_roles(
        self,
        json,
        manager_id=MANAGER_2_ID_DEPLOYMENT_X,
    ):
        return self.flask_client.post(
            f"{self.base_path}/add-role",
            json=json,
            headers=self.get_headers_for_token(manager_id),
        )

    def test_success_add_roles(self):
        role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(request_body)
        self.assertEqual(200, response.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(1, len(user[User.ROLES]))
        self.assertIn(role.to_dict(), user[User.ROLES])

    def test_success_add_roles_to_all_staff(self):
        role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
        request_body = {
            AddRolesToUsersRequestObject.ALL_USERS: True,
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(request_body)
        self.assertEqual(200, response.status_code)
        for user_id in [
            MANAGER_1_ID_DEPLOYMENT_X,
            CONTRIBUTOR_1_ID_DEPLOYMENT_X,
        ]:
            user = self.get_user_from_db(user_id)
            self.assertEqual(1, len(user[User.ROLES]))
            self.assertIn(role.to_dict(), user[User.ROLES])

    def test_success_add_existing_role(self):
        role: RoleAssignment = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(request_body)
        self.assertEqual(200, response.status_code)
        user = self.get_user_from_db(MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(1, len(user[User.ROLES]))

    def test_success_update_org_staff_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [
                ORGANIZATION_STAFF_ID,
            ],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(json=request_body, manager_id=ACCESS_CONTROLLER_ID)
        self.assertEqual(200, response.status_code)

    def test_failure_update_user_roles_dif_target_deployment(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(request_body)
        self.assertEqual(403, response.status_code)
        self.assertEqual(100004, response.json["code"])

    def test_failure_update_user_roles_dif_users_deployment(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_2_ID_DEPLOYMENT_Y],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(request_body)
        self.assertEqual(403, response.status_code)

    def test_failure_update_user_roles_by_contributor(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, "5d386cc6ff885918d96edb44")
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(
            json=request_body, manager_id=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(403, response.status_code)

    def test_failure_update_user_roles_to_patient_user(self):
        role = RoleAssignment.create_role(RoleName.USER, "5d386cc6ff885918d96edb44")
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(
            json=request_body, manager_id=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(403, response.status_code)

    def test_failure_update_user_roles_to_super_admin(self):
        role = RoleAssignment.create_role(
            RoleName.SUPER_ADMIN, "5d386cc6ff885918d96edb44"
        )
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(
            json=request_body, manager_id=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(403, response.status_code)

    def test_failure_update_user_roles_when_invalid_role_provided(self):
        role = {
            "roleId": "InvalidRole",
            "resource": f"deployment/{DEPLOYMENT_ID}",
        }
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role],
        }
        response = self.add_roles(request_body)
        self.assertEqual(403, response.status_code)

    def test_success_update_user_organization_role_by_access_controller(self):
        role = RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [ORGANIZATION_STAFF_ID],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(json=request_body, manager_id=ACCESS_CONTROLLER_ID)
        self.assertEqual(200, response.status_code)

    def test_failure_update_user_organization_role_by_admin(self):
        role = RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(json=request_body)
        self.assertEqual(400, response.status_code)

    def test_failure_update_user_deployment_staff_by_admin(self):
        role = RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_ID)
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: [MANAGER_1_ID_DEPLOYMENT_X],
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(
            json=request_body, manager_id=MANAGER_2_ID_DEPLOYMENT_X
        )
        self.assertEqual(400, response.status_code)

    def test_failure_update_multiple_users_roles_to_admin(self):
        role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_ID)
        user_ids = [
            MANAGER_1_ID_DEPLOYMENT_X,
            CONTRIBUTOR_1_ID_DEPLOYMENT_X,
        ]
        request_body = {
            AddRolesToUsersRequestObject.USER_IDS: user_ids,
            AddRolesToUsersRequestObject.ROLES: [role.to_dict()],
        }
        response = self.add_roles(
            json=request_body, manager_id=MANAGER_2_ID_DEPLOYMENT_X
        )
        self.assertEqual(403, response.status_code)
