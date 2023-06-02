from unittest import TestCase

from extensions.authorization.events import GetDeploymentCustomRoleEvent
from extensions.authorization.models.role.default_permissions import (
    PermissionType,
    PolicyType,
)
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, CustomRolesExtension
from extensions.authorization.validators import (
    check_role_id_valid_for_resource,
)
from extensions.deployment.models.deployment import Deployment
from extensions.tests.authorization.IntegrationTests.test_helpers import DEPLOYMENT_ID
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import RoleDoesNotExist
from sdk.common.utils import inject


test_roles = [
    Role.from_dict(
        {
            Role.ID: "6009d18864a6786c2a2be181",
            Role.NAME: "Nurse",
            Role.PERMISSIONS: ["VIEW_PATIENT_DATA", "MANAGE_PATIENT_DATA"],
        }
    ),
    Role.from_dict(
        {
            Role.ID: "6009d18864a6786c2a2be180",
            Role.NAME: "Readonly",
            Role.PERMISSIONS: ["VIEW_PATIENT_DATA"],
        }
    ),
]


class RolesTestCase(TestCase):
    event_bus = EventBusAdapter()

    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            binder.bind(EventBusAdapter, cls.event_bus)

        inject.clear_and_configure(bind)

        cls.event_bus.subscribe(GetDeploymentCustomRoleEvent, lambda: test_roles)

    def setUp(self) -> None:
        self.deployment = Deployment(roles=test_roles)

    def test_success_create_role_with_default_permissions(self):
        role_data = {
            Role.NAME: "Nurse",
            Role.PERMISSIONS: [],
            Role.USER_TYPE: Role.UserType.MANAGER,
        }
        role = Role.from_dict(role_data)
        self.assertFalse(role.has_extra_permissions())
        for permission in PermissionType.common_permissions():
            self.assertIn(permission, role.permissions)

    def test_success_create_role_with_default_permissions_appended(self):
        role_data = {
            Role.NAME: "Nurse",
            Role.PERMISSIONS: [PermissionType.EDIT_ROLE_PERMISSIONS.value],
            Role.USER_TYPE: Role.UserType.MANAGER,
        }
        role = Role.from_dict(role_data)
        self.assertEqual(5, len(role.permissions))
        self.assertTrue(role.has_extra_permissions())
        for permission in PermissionType.common_permissions():
            self.assertIn(permission, role.permissions)

    def test_success_create_role_with_no_duplicate_permissions(self):
        common_permissions = [
            perm.value for perm in PermissionType.common_permissions()
        ]
        role_data = {
            Role.NAME: "Nurse",
            Role.PERMISSIONS: [*common_permissions, *common_permissions],
            Role.USER_TYPE: Role.UserType.MANAGER,
        }
        role = Role.from_dict(role_data)
        self.assertEqual(4, len(role.permissions))
        self.assertFalse(role.has_extra_permissions())

    def test_success_append_permission(self):
        role = Role(permissions=[PermissionType.EDIT_ROLE_PERMISSIONS])
        new_permission = PermissionType.ADD_STAFF_MEMBERS
        role.add_permissions([new_permission])
        self.assertIn(new_permission, role.permissions)

    def test_success_role_has_polices(self):
        expected_policies = [
            PolicyType.EDIT_CUSTOM_ROLES,
            PolicyType.VIEW_CUSTOM_ROLES,
        ]
        role = Role(permissions=[PermissionType.EDIT_ROLE_PERMISSIONS])
        for item in expected_policies:
            self.assertTrue(role.has([item]))

        self.assertTrue(role.has(expected_policies))
        self.assertTrue(role.has_extra_permissions())

    def test_success_role_has_polices_complex(self):
        expected_policies = [
            PolicyType.EDIT_CUSTOM_ROLES,
            PolicyType.VIEW_CUSTOM_ROLES,
            PolicyType.INVITE_STAFFS,
            PolicyType.ASSIGN_ROLES_TO_STAFF,
            PolicyType.ADD_REMOVE_PATIENT,
            PolicyType.CHANGE_PATIENT_STATUS,
            PolicyType.EDIT_PATIENT_NOTE,
            PolicyType.EDIT_PATIENT_PROFILE,
            PolicyType.ASSIGN_PATIENT_TO_STAFF,
            PolicyType.MOVE_PATIENT_TO_OTHER_GROUP,
        ]
        role = Role(
            permissions=[
                PermissionType.ADD_STAFF_MEMBERS,
                PermissionType.EDIT_ROLE_PERMISSIONS,
                PermissionType.MANAGE_PATIENT_DATA,
            ]
        )
        for item in expected_policies:
            self.assertTrue(role.has([item]))

        self.assertTrue(role.has(expected_policies))
        self.assertTrue(role.has_extra_permissions())

    def test_check_role_valid_default_roles(self):
        for role in DefaultRoles():
            try:
                check_role_id_valid_for_resource(role, DEPLOYMENT_ID)
            except Exception as e:
                self.fail(str(e))

    def test_check_role_valid_custom_roles(self):
        for role in self.deployment.roles:
            try:
                check_role_id_valid_for_resource(role.id, DEPLOYMENT_ID)
            except Exception as e:
                self.fail(str(e))

    def test_check_role_invalid(self):
        role_id = "6009d18864a6786c2a2be161"

        is_valid = check_role_id_valid_for_resource(
            role_id, DEPLOYMENT_ID, "deployment"
        )
        self.assertFalse(is_valid)


class DeploymentRolesExtensionTestCase(TestCase):
    def test_failure_validate_non_existing_roles(self):
        roles_extension = CustomRolesExtension()
        role = Role(id="12345")
        roles_extension.roles = [role]
        with self.assertRaises(RoleDoesNotExist):
            roles_extension.validate_roles([Role(id="111")])

    def test_success_validate_roles(self):
        roles_extension = CustomRolesExtension()
        role = Role(id="12345")
        roles_extension.roles = [role]
        try:
            roles_extension.validate_roles([role])
        except RoleDoesNotExist:
            self.assertTrue(False)

    def test_str_roles(self):
        role_id = "12345"
        role_name = "name"
        role_permissions = [
            PermissionType.EDIT_ROLE_PERMISSIONS,
            PermissionType.VIEW_OWN_DATA,
        ]
        role_user_type = Role.UserType.MANAGER

        role = Role(id=role_id)
        role.name = role_name
        role.permissions = role_permissions
        role.userType = role_user_type

        self.assertEqual(
            f"{role}",
            (
                f"[{Role.__name__} {Role.ID}: {role_id}, "
                f"{Role.NAME}: {role_name}, "
                f"{Role.PERMISSIONS}: {[permission.value for permission in role_permissions]}, "
                f"{Role.USER_TYPE}: {role_user_type}]"
            ),
        )
