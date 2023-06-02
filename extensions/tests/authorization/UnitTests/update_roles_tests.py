from unittest import TestCase
from unittest.mock import MagicMock, patch
from extensions.authorization.use_cases.add_roles_to_users_use_case import (
    AddRolesToUsersUseCase,
)

from flask import Flask, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.router.user_profile_request import (
    AddRolesRequestObject,
    AddRolesToUsersRequestObject,
    RemoveRolesRequestObject,
    UpdateUserRoleRequestObject,
)
from extensions.authorization.use_cases.add_role_use_case import AddRolesUseCase
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRoleException
from sdk.common.utils import inject

DEPLOYMENT_ID = "deploymentTestID"
ORGANIZATION_ID = "organizationTestID"
app = Flask(__name__)

DEPLOYMENT_1_ID = "501919b5c03550c421c075aa"
DEPLOYMENT_2_ID = "501919b5c03550c421c075bb"
DEPLOYMENT_3_ID = "501919b5c03550c421c075cc"
ORG_1_ID = "501919b5c03550c421c075ee"
ORG_2_ID = "501919b5c03550c421c075ff"

inject.clear_and_configure(lambda x: x)


def user(role: str):
    resource_id = ORG_1_ID if role in RoleName.org_roles() else DEPLOYMENT_1_ID
    return User(id="testUserId", roles=[RoleAssignment.create_role(role, resource_id)])


def get_authz_user(role_id, resource_id):
    role = RoleAssignment.create_role(role_id, resource_id)
    return AuthorizedUser(User(roles=[role]))


class AddRoleRequestObjectTestCase(TestCase):
    deployment_repo = None
    organization_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()
        cls.organization_repo = MagicMock()
        cls.organization_repo.retrieve_organization.return_value = Organization(
            deploymentIds=[DEPLOYMENT_1_ID]
        )

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)
            binder.bind_to_provider(
                OrganizationRepository, lambda: cls.organization_repo
            )
            binder.bind_to_provider(ConsentRepository, MagicMock())
            binder.bind_to_provider(EConsentRepository, MagicMock())

        inject.clear_and_configure(bind)

    def get_authz_user(self, role_id, resource_id):
        role = RoleAssignment.create_role(role_id, resource_id)
        return AuthorizedUser(User(roles=[role]))

    def test_failure_update_role_to_admin_of_multiple_deployments(self):
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID).to_dict(),
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID).to_dict(),
        ]
        body = {
            AddRolesRequestObject.ROLES: new_roles,
            AddRolesRequestObject.USER_ID: "testUserId",
            AddRolesRequestObject.SUBMITTER: get_authz_user(
                RoleName.ADMIN, DEPLOYMENT_1_ID
            ),
        }
        with self.assertRaises(InvalidRoleException):
            AddRolesRequestObject.from_dict(body)

    def test_success_update_role_to_call_center_of_multiple_deployments(self):
        new_roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID).to_dict(),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID).to_dict(),
        ]
        body = {
            AddRolesRequestObject.ROLES: new_roles,
            AddRolesRequestObject.USER_ID: "testUserId",
            AddRolesRequestObject.SUBMITTER: get_authz_user(
                RoleName.ACCESS_CONTROLLER, DEPLOYMENT_1_ID
            ),
        }
        req_obj = AddRolesRequestObject.from_dict(body)
        self.assertIsInstance(req_obj, AddRolesRequestObject)
        self.assertIsNotNone(req_obj.userId)
        self.assertIsNotNone(req_obj.submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_success_check_permission_obj(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        AddRolesRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_success_check_permission_dict(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID).to_dict()
        ]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        AddRolesRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_failure_check_permission_permission_denied_ac(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID)]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        with self.assertRaises(PermissionDenied):
            AddRolesRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_failure_check_permission_permission_denied_admin(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID).to_dict()
        ]
        submitter = self.get_authz_user(RoleName.ADMIN, DEPLOYMENT_1_ID)
        with self.assertRaises(PermissionDenied):
            AddRolesRequestObject.check_permission(new_roles, submitter)


class AddRoleUseCaseTestCase(TestCase):
    deployment_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)
            binder.bind_to_provider(OrganizationRepository, MagicMock())

        inject.clear_and_configure(bind)

    @property
    def use_case(self):
        return AddRolesUseCase(MagicMock(), MagicMock(), MagicMock())

    def test_success_update_admin_to_contributor(self):
        roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_contributor_to_admin(self):
        roles = [RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_deployment_staff_to_access_controller(self):
        roles = [RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_organization_staff_to_access_controller(self):
        roles = [
            RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, DEPLOYMENT_1_ID)
        ]
        new_role = RoleAssignment.create_role(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_add_deployment_staff_role_to_deployment_staff(self):
        roles = [
            RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_3_ID
        )
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(3, len(roles))

    def test_success_add_call_center_role_to_call_center(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_3_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(3, len(roles))

    def test_success_add_call_center_role_to_call_center_same_deployment(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(2, len(roles))

    def test_success_replace_call_center_with_deployment_staff(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID
        )
        with self.assertRaises(InvalidRoleException):
            self.use_case.add_role_to_list(new_role, roles)

    def test_success_replace_organization_staff_with_deployment_staff(self):
        roles = [RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORG_1_ID)]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID
        )
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(1, len(roles))
        self.assertEqual(new_role, roles[0])


class AddRolesToUsersRequestObjectTestCase(TestCase):
    deployment_repo = None
    organization_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()
        cls.organization_repo = MagicMock()
        cls.organization_repo.retrieve_organization.return_value = Organization(
            deploymentIds=[DEPLOYMENT_1_ID]
        )

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)
            binder.bind_to_provider(
                OrganizationRepository, lambda: cls.organization_repo
            )
            binder.bind_to_provider(ConsentRepository, MagicMock())
            binder.bind_to_provider(EConsentRepository, MagicMock())

        inject.clear_and_configure(bind)

    def get_authz_user(self, role_id, resource_id):
        role = RoleAssignment.create_role(role_id, resource_id)
        return AuthorizedUser(User(roles=[role]))

    def test_failure_update_role_to_admin_of_multiple_deployments(self):
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID).to_dict(),
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID).to_dict(),
        ]
        body = {
            AddRolesToUsersRequestObject.allUsers: False,
            AddRolesToUsersRequestObject.ROLES: new_roles,
            AddRolesToUsersRequestObject.USER_IDS: ["501919b5c03550c421c071aa"],
            AddRolesToUsersRequestObject.SUBMITTER: get_authz_user(
                RoleName.ADMIN, DEPLOYMENT_1_ID
            ),
        }
        with self.assertRaises(InvalidRoleException):
            AddRolesToUsersRequestObject.from_dict(body)

    def test_success_update_role_to_call_center_of_multiple_deployments(self):
        new_roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID).to_dict(),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID).to_dict(),
        ]
        body = {
            AddRolesToUsersRequestObject.ROLES: new_roles,
            AddRolesToUsersRequestObject.USER_IDS: ["501919b5c03550c421c071aa"],
            AddRolesToUsersRequestObject.SUBMITTER: get_authz_user(
                RoleName.ACCESS_CONTROLLER, DEPLOYMENT_1_ID
            ),
        }
        req_obj = AddRolesToUsersRequestObject.from_dict(body)
        self.assertIsInstance(req_obj, AddRolesToUsersRequestObject)
        self.assertIsNotNone(req_obj.userIds)
        self.assertIsNotNone(req_obj.submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_success_check_permission_obj(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        AddRolesToUsersRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_success_check_permission_dict(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID).to_dict()
        ]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        AddRolesToUsersRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_failure_check_permission_permission_denied_ac(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID)]
        submitter = self.get_authz_user(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        with self.assertRaises(PermissionDenied):
            AddRolesToUsersRequestObject.check_permission(new_roles, submitter)

    @patch("extensions.authorization.models.authorized_user._get_organization")
    def test_failure_check_permission_permission_denied_admin(self, mock_get_org):
        mock_get_org.return_value = Organization(deploymentIds=[DEPLOYMENT_1_ID])
        new_roles = [
            RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_2_ID).to_dict()
        ]
        submitter = self.get_authz_user(RoleName.ADMIN, DEPLOYMENT_1_ID)
        with self.assertRaises(PermissionDenied):
            AddRolesToUsersRequestObject.check_permission(new_roles, submitter)


class AddRolesToUsersTestCase(TestCase):
    deployment_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)
            binder.bind_to_provider(OrganizationRepository, MagicMock())

        inject.clear_and_configure(bind)

    @property
    def use_case(self):
        return AddRolesToUsersUseCase(MagicMock(), MagicMock(), MagicMock())

    def test_success_update_admin_to_contributor(self):
        roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_contributor_to_admin(self):
        roles = [RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_deployment_staff_to_access_controller(self):
        roles = [RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID)]
        new_role = RoleAssignment.create_role(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_update_organization_staff_to_access_controller(self):
        roles = [
            RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, DEPLOYMENT_1_ID)
        ]
        new_role = RoleAssignment.create_role(RoleName.ACCESS_CONTROLLER, ORG_1_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(new_role, roles[0])

    def test_success_add_deployment_staff_role_to_deployment_staff(self):
        roles = [
            RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_3_ID
        )
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(3, len(roles))

    def test_success_add_call_center_role_to_call_center(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_3_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(3, len(roles))

    def test_success_add_call_center_role_to_call_center_same_deployment(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID)
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(2, len(roles))

    def test_success_replace_call_center_with_deployment_staff(self):
        roles = [
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_1_ID),
            RoleAssignment.create_role(RoleName.CALL_CENTER, DEPLOYMENT_2_ID),
        ]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID
        )
        with self.assertRaises(InvalidRoleException):
            self.use_case.add_role_to_list(new_role, roles)

    def test_success_replace_organization_staff_with_deployment_staff(self):
        roles = [RoleAssignment.create_role(RoleName.ORGANIZATION_STAFF, ORG_1_ID)]
        new_role = RoleAssignment.create_role(
            RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID
        )
        self.use_case.add_role_to_list(new_role, roles)
        self.assertEqual(1, len(roles))
        self.assertEqual(new_role, roles[0])


class RemoveRolesRequestObjectTestCase(TestCase):
    deployment_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(DeploymentRepository, cls.deployment_repo)
            binder.bind_to_provider(OrganizationRepository, MagicMock())

        inject.clear_and_configure(bind)

    def test_success_remove_admin_by_admin(self):
        roles = [RoleAssignment.create_role(RoleName.ADMIN, DEPLOYMENT_1_ID).to_dict()]
        body = {
            RemoveRolesRequestObject.ROLES: roles,
            RemoveRolesRequestObject.USER_ID: "testUserId",
            RemoveRolesRequestObject.SUBMITTER: get_authz_user(
                RoleName.ADMIN, DEPLOYMENT_1_ID
            ),
        }
        req_obj = RemoveRolesRequestObject.from_dict(body)
        self.assertIsNotNone(req_obj.userId)
        self.assertEqual(1, len(req_obj.roles))
        self.assertEqual(RoleName.ADMIN, req_obj.submitter.get_role().id)

    def test_success_remove_multiple_roles(self):
        roles = [
            RoleAssignment.create_role(
                RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_1_ID
            ).to_dict(),
            RoleAssignment.create_role(
                RoleName.DEPLOYMENT_STAFF, DEPLOYMENT_2_ID
            ).to_dict(),
        ]
        body = {
            RemoveRolesRequestObject.ROLES: roles,
            RemoveRolesRequestObject.USER_ID: "testUserId",
            RemoveRolesRequestObject.SUBMITTER: get_authz_user(
                RoleName.ACCESS_CONTROLLER, DEPLOYMENT_1_ID
            ),
        }
        req_obj = RemoveRolesRequestObject.from_dict(body)
        self.assertIsNotNone(req_obj.userId)
        self.assertEqual(2, len(req_obj.roles))


class MockOrgRepo(MagicMock):
    def retrieve_organization(self, organization_id):
        return Organization(deploymentIds=[DEPLOYMENT_ID])


class UpdateRoleTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(OrganizationRepository, MockOrgRepo())
            binder.bind(DeploymentRepository, MagicMock())

        inject.clear_and_configure(bind)

    def test_success_update_role_organization_staff(self):
        inviter = get_authz_user(RoleName.ACCESS_CONTROLLER, ORGANIZATION_ID)
        with app.app_context():
            g.authz_user = inviter
            role = RoleAssignment.create_role(
                RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID
            )
            data = {
                UpdateUserRoleRequestObject.ROLES: [role.to_dict()],
                UpdateUserRoleRequestObject.SUBMITTER: inviter,
            }
            UpdateUserRoleRequestObject.from_dict(data)

    def test_failure_update_role_admin_with_organization_id(self):
        inviter = get_authz_user(RoleName.ACCESS_CONTROLLER, ORGANIZATION_ID)
        with app.app_context():
            g.authz_user = inviter
            role = RoleAssignment.create_role(RoleName.ADMIN, ORGANIZATION_ID)
            data = {
                UpdateUserRoleRequestObject.ROLES: [role.to_dict()],
                UpdateUserRoleRequestObject.SUBMITTER: inviter,
            }
            with self.assertRaises(PermissionDenied):
                UpdateUserRoleRequestObject.from_dict(data)
