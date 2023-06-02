import unittest
from unittest.mock import MagicMock

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.use_cases.invitation_use_cases import (
    CommonInvitationUseCase,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    InvalidRoleException,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig


class CommonInvitationUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.deployment_repo = MagicMock()

        def configure_with_binder(binder: Binder):
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(EmailInvitationAdapter, MagicMock())
            binder.bind(TokenAdapter, MagicMock())
            binder.bind(PhoenixServerConfig, MagicMock())
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(AuthorizationRepository, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    def test_success_get_custom_role_or_raise_error(self):
        use_case = CommonInvitationUseCase()
        role_assignment = MagicMock()
        use_case.get_custom_role_or_raise_error(role_assignment)
        self.deployment_repo.retrieve_deployment.assert_called_with(
            deployment_id=role_assignment.resource_id()
        )

    def test_failure_get_custom_role_or_raise_error_no_resource(self):
        use_case = CommonInvitationUseCase()
        role_assignment = MagicMock()
        role_assignment.is_deployment.return_value = None
        role_assignment.is_org.return_value = None
        with self.assertRaises(InvalidRequestException):
            use_case.get_custom_role_or_raise_error(role_assignment)

    def test_failure_get_custom_role_or_raise_error_no_role(self):
        use_case = CommonInvitationUseCase()
        role_assignment = MagicMock()
        resource = MagicMock()
        resource.find_role_by_id.return_value = None
        self.deployment_repo.retrieve_deployment.return_value = resource
        with self.assertRaises(InvalidRoleException):
            use_case.get_custom_role_or_raise_error(role_assignment)


if __name__ == "__main__":
    unittest.main()
