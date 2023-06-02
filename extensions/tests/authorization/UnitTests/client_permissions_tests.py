import unittest

from extensions.authorization.callbacks import are_client_permissions_valid
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from sdk.phoenix.config.server_config import Client


def get_user(role_name: RoleName):
    role = RoleAssignment(
        roleId=role_name, resource="deployment/5eff28a09f02607bf370c43c"
    )
    user = User(roles=[role])
    return AuthorizedUser(user)


def get_client_for_roles(role_names: list[RoleName]):
    return Client(
        clientType=Client.ClientType.MANAGER_WEB,
        clientId="client1",
        roleIds=role_names,
    )


class ClientPermissionsTestCase(unittest.TestCase):
    def test_client_permissions_valid(self):
        manager_user = get_user(RoleName.USER)
        client = get_client_for_roles([RoleName.USER])
        valid = are_client_permissions_valid(client, manager_user)
        self.assertTrue(valid)

    def test_client_permissions_not_valid(self):
        manager_user = get_user(RoleName.USER)
        client = get_client_for_roles([RoleName.CONTRIBUTOR])
        valid = are_client_permissions_valid(client, manager_user)
        self.assertFalse(valid)

        manager_user = get_user(RoleName.SUPER_ADMIN)
        client = get_client_for_roles([RoleName.CONTRIBUTOR])
        valid = are_client_permissions_valid(client, manager_user)
        self.assertFalse(valid)
