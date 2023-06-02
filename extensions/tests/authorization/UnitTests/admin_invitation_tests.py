from pathlib import Path
from unittest import TestCase

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.router.admin_invitation_request_objects import (
    SendAdminInvitationsRequestObject,
)
from sdk.common.exceptions.exceptions import (
    PermissionDenied,
    InvalidClientIdException,
    InvalidProjectIdException,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

ORGANIZATION_ID = "6009d18864a6786c2a2be161"


def get_submitter(role: str):
    role = RoleAssignment(
        roleId=role,
        resource=f"organization/{ORGANIZATION_ID}",
        userType=Role.UserType.SUPER_ADMIN,
    )
    return AuthorizedUser(User(roles=[role]))


class SendAdminInvitationsRequestObjectTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            config_path = Path(__file__).parent.joinpath("config.test.yaml")
            config = PhoenixServerConfig.get(config_path, {})
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(PhoenixServerConfig, config)

        inject.clear_and_configure(bind)

    @classmethod
    def tearDownClass(cls) -> None:
        inject.clear()

    def test_success_SuperAdmin_invites_HumaSupport(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.HUMA_SUPPORT,
        )

    def test_success_SuperAdmin_invites_AccountManager(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.ACCOUNT_MANAGER,
        )

    def test_success_SuperAdmin_invites_OrganizationOwner(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.ORGANIZATION_OWNER,
        )

    def test_success_SuperAdmin_invites_OrganizationEditor(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.ORGANIZATION_EDITOR,
        )

    def test_success_HumaSupport_invites_AccountManager(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.HUMA_SUPPORT,
            target=RoleName.ACCOUNT_MANAGER,
        )

    def test_success_HumaSupport_invites_OrganizationOwner(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.HUMA_SUPPORT,
            target=RoleName.ORGANIZATION_OWNER,
        )

    def test_success_HumaSupport_invites_OrganizationEditor(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.HUMA_SUPPORT,
            target=RoleName.ORGANIZATION_EDITOR,
        )

    def test_success_OrganizationOwner_invites_OrganizationEditor(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.ORGANIZATION_OWNER,
            target=RoleName.ORGANIZATION_EDITOR,
        )

    def test_success_OrganizationOwner_invites_OrganizationOwner(self):
        self.assertNoPermissionErrorRaised(
            sender=RoleName.ORGANIZATION_OWNER,
            target=RoleName.ORGANIZATION_OWNER,
        )

    def test_failure_different_organizations(self):
        data = self.request_data(
            role=RoleName.HUMA_SUPPORT,
            submitter_role=RoleName.ORGANIZATION_EDITOR,
            org_id="6009d18864a6786c2a2be115",
        )
        with self.assertRaises(PermissionDenied):
            SendAdminInvitationsRequestObject.from_dict(data)

    def test_failure_HumaSupport_invites_SuperAdmin(self):
        self.assertPermissionError(
            sender=RoleName.HUMA_SUPPORT,
            target=RoleName.SUPER_ADMIN,
        )

    def test_failure_AccountManager_invites_SuperAdmin(self):
        self.assertPermissionError(
            sender=RoleName.ACCOUNT_MANAGER,
            target=RoleName.SUPER_ADMIN,
        )

    def test_failure_AccountManager_invites_HumaSupport(self):
        self.assertPermissionError(
            sender=RoleName.ACCOUNT_MANAGER,
            target=RoleName.HUMA_SUPPORT,
        )

    def test_failure_AccountManager_invites_AccountManager(self):
        self.assertPermissionError(
            sender=RoleName.ACCOUNT_MANAGER,
            target=RoleName.ACCOUNT_MANAGER,
        )

    def test_failure_AccountManager_invites_OrganizationEditor(self):
        self.assertPermissionError(
            sender=RoleName.ACCOUNT_MANAGER,
            target=RoleName.ORGANIZATION_EDITOR,
        )

    def test_failure_OrganizationOwner_invites_SuperAdmin(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_OWNER,
            target=RoleName.SUPER_ADMIN,
        )

    def test_failure_OrganizationOwner_invites_HumaSupport(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_OWNER,
            target=RoleName.HUMA_SUPPORT,
        )

    def test_failure_OrganizationOwner_invites_AccountManager(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_OWNER,
            target=RoleName.ACCOUNT_MANAGER,
        )

    def test_failure_OrganizationEditor_invites_SuperAdmin(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_EDITOR,
            target=RoleName.SUPER_ADMIN,
        )

    def test_failure_OrganizationEditor_invites_HumaSupport(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_EDITOR,
            target=RoleName.HUMA_SUPPORT,
        )

    def test_failure_OrganizationEditor_invites_AccountManager(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_EDITOR,
            target=RoleName.ACCOUNT_MANAGER,
        )

    def test_failure_OrganizationEditor_invites_OrganizationOwner(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_EDITOR,
            target=RoleName.ORGANIZATION_OWNER,
        )

    def test_failure_OrganizationEditor_invites_OrganizationEditor(self):
        self.assertPermissionError(
            sender=RoleName.ORGANIZATION_EDITOR,
            target=RoleName.ORGANIZATION_EDITOR,
        )

    def test_failure_invite_user(self):
        self.assertPermissionError(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.USER,
        )

    def test_failure_invite_manager(self):
        self.assertPermissionError(
            sender=RoleName.SUPER_ADMIN,
            target=RoleName.ADMIN,
        )

    @staticmethod
    def request_data(role: str, submitter_role: str, org_id=None):
        submitter = get_submitter(submitter_role)
        return {
            SendAdminInvitationsRequestObject.CLIENT_ID: "test1",
            SendAdminInvitationsRequestObject.PROJECT_ID: "test1",
            SendAdminInvitationsRequestObject.ROLE_ID: role,
            SendAdminInvitationsRequestObject.ORGANIZATION_ID: org_id
            or ORGANIZATION_ID,
            SendAdminInvitationsRequestObject.EMAILS: ["email@test.com"],
            SendAdminInvitationsRequestObject.SUBMITTER: submitter,
        }

    def assertNoPermissionErrorRaised(self, sender: str, target: str):
        data = self.request_data(target, sender)
        try:
            SendAdminInvitationsRequestObject.from_dict(data)
        except PermissionDenied as e:
            self.fail(e)

    def assertPermissionError(self, sender: str, target: str):
        data = self.request_data(target, sender)
        with self.assertRaises(PermissionDenied):
            SendAdminInvitationsRequestObject.from_dict(data)

    def test_failure_invalid_client_id(self):
        data = {
            **self.request_data(RoleName.ORGANIZATION_EDITOR, RoleName.HUMA_SUPPORT),
            SendAdminInvitationsRequestObject.CLIENT_ID: "invalid client id",
        }
        with self.assertRaises(InvalidClientIdException):
            SendAdminInvitationsRequestObject.from_dict(data)

    def test_failure_invalid_project_id(self):
        data = {
            **self.request_data(RoleName.ORGANIZATION_EDITOR, RoleName.HUMA_SUPPORT),
            SendAdminInvitationsRequestObject.PROJECT_ID: "invalid project id",
        }
        with self.assertRaises(InvalidProjectIdException):
            SendAdminInvitationsRequestObject.from_dict(data)
