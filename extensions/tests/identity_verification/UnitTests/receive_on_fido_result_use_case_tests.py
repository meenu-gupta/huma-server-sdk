import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)
from extensions.identity_verification.repository.verification_log_repository import (
    VerificationLogRepository,
)
from extensions.identity_verification.use_cases.receive_onfido_result_use_case import (
    ReceiveOnfidoResultUseCase,
)
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationAdapter
from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)
from sdk.common.localization.utils import Language
from sdk.common.utils import inject

ONFIDO_RESULT_USER_CASE = (
    "extensions.identity_verification.use_cases.receive_onfido_result_use_case"
)


class ReceiveOnfidoResultUseCasePrivateMethodsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.log_repo = MagicMock()

        def bind(binder):
            binder.bind_to_provider(AuthorizationRepository, lambda: self.auth_repo)
            binder.bind_to_provider(VerificationLogRepository, lambda: self.log_repo)
            binder.bind_to_provider(
                IdentityVerificationEmailAdapter, lambda: MagicMock()
            )
            binder.bind_to_provider(IdentityVerificationAdapter, lambda: MagicMock())

        inject.clear_and_configure(bind)

    def get_use_case(self):
        return ReceiveOnfidoResultUseCase(self.auth_repo, self.log_repo)

    def test_set_verification_status_if_complete_succeeded(self):
        result = VerificationLog.ResultType.CLEAR.value
        applicant_id = "123"
        use_case = self.get_use_case()
        use_case._set_verification_status_if_complete(result, applicant_id)
        self.auth_repo.update_user_onfido_verification_status.assert_called_once_with(
            applicant_id=applicant_id,
            verification_status=User.VerificationStatus.ID_VERIFICATION_SUCCEEDED,
        )

    def test_set_verification_status_if_complete_failed(self):
        result = VerificationLog.ResultType.CONSIDER.value
        applicant_id = "123"
        use_case = self.get_use_case()
        use_case._set_verification_status_if_complete(result, applicant_id)
        self.auth_repo.update_user_onfido_verification_status.assert_called_once_with(
            applicant_id=applicant_id,
            verification_status=User.VerificationStatus.ID_VERIFICATION_FAILED,
        )

    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    @patch(f"{ONFIDO_RESULT_USER_CASE}.AuthorizedUser")
    def test_send_verification_result_push_notification(
        self, auth_user, notification_service
    ):
        auth_user.get_language.return_value = Language.EN
        user = MagicMock()
        use_case = self.get_use_case()
        use_case._send_notifications_to_user(user)
        notification_service().push_for_user.assert_called_once()


if __name__ == "__main__":
    unittest.main()
