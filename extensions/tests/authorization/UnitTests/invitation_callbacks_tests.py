from unittest import TestCase
from unittest.mock import patch, MagicMock

from extensions.authorization.callbacks.callbacks import _prepare_new_user
from extensions.authorization.models.invitation import Invitation
from extensions.authorization.models.user import RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.authorization.UnitTests.invitation_use_case_tests import (
    get_deployment,
)
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import Client
from sdk.tests.auth.test_helpers import USER_EMAIL


def get_organization():
    return Organization(
        name="test",
        privacyPolicyUrl="privacy_url_val_organization",
        eulaUrl="eula_url_val_organization",
        termAndConditionUrl="term_val_organization",
    )


class MockService:
    def retrieve_deployment_with_code(self, code=None):
        return Deployment(id="12345678"), "User", "12345678"


class InvitationCallbackTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_auth_repo = MagicMock()
        cls.mocked_deployment_repo = MagicMock()
        cls.mocked_organization_repo = MagicMock()

        cls.mocked_organization_repo.retrieve_organization.return_value = (
            get_organization()
        )

        def configure_with_binder(binder: Binder):
            binder.bind(AuthRepository, cls.mocked_auth_repo)
            binder.bind(DeploymentRepository, cls.mocked_deployment_repo)
            binder.bind(OrganizationRepository, cls.mocked_organization_repo)
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(AuthorizationRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

        cls.sample_client = Client(
            clientId="ctest1", clientType=Client.ClientType.USER_IOS
        )

    @patch("extensions.authorization.callbacks.callbacks.retrieve_invitation")
    @patch("extensions.authorization.callbacks.callbacks.inject", MagicMock())
    def test_success_prepare_new_user_with_invitation(self, invitation_mock):
        deployment_id = "12345678"
        role_id = "Admin"
        invitation = Invitation(
            roles=[RoleAssignment.create_role(role_id, deployment_id)]
        )
        invitation_mock.return_value = invitation
        expected_roles = [
            RoleAssignment(
                roleId=role_id,
                resource=f"deployment/{deployment_id}",
            )
        ]
        user_data = {
            AuthUser.EMAIL: "test@user.com",
            AuthUser.USER_ATTRIBUTES: {},
            AuthUser.VALIDATION_DATA: {"invitationCode": 12345678},
        }
        user = _prepare_new_user(user_data, self.sample_client)
        self.assertIsNone(user.carePlanGroupId)
        self.assertEqual(expected_roles, user.roles)

    @patch("extensions.authorization.callbacks.callbacks.retrieve_invitation")
    @patch("extensions.deployment.service.deployment_service.DeploymentService")
    def test_prepare_new_user_with_invitation_verifies_email(
        self, deployment_service_mock, invitation_mock
    ):
        invitation = Invitation(
            roles=[RoleAssignment.create_role("Admin", "12345678")], email=USER_EMAIL
        )
        invitation_mock.return_value = invitation

        deployment_service_mock.retrieve_deployment = get_deployment()

        user_data = {
            AuthUser.EMAIL: USER_EMAIL,
            AuthUser.USER_ATTRIBUTES: {},
            AuthUser.VALIDATION_DATA: {"invitationCode": 12345678},
        }
        _prepare_new_user(
            user_data, Client(clientId="ctest1", clientType=Client.ClientType.USER_IOS)
        )
        self.mocked_auth_repo.confirm_email.assert_called_once_with(
            uid=None, email=USER_EMAIL
        )

    @patch(
        "extensions.authorization.callbacks.callbacks.DeploymentService", MockService
    )
    @patch("extensions.authorization.callbacks.callbacks.inject", MagicMock())
    def test_success_prepare_new_user_with_activation(self):
        result = MockService().retrieve_deployment_with_code()
        expected_roles = [
            RoleAssignment(
                roleId=result[1],
                resource=f"deployment/{result[0].id}",
            )
        ]
        user_data = {
            AuthUser.EMAIL: "test@user.com",
            AuthUser.USER_ATTRIBUTES: {},
            AuthUser.VALIDATION_DATA: {"activationCode": 12345678},
        }
        user = _prepare_new_user(user_data, self.sample_client)
        self.assertEqual(result[2], user.carePlanGroupId)
        self.assertEqual(expected_roles, user.roles)
