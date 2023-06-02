import i18n

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)
from extensions.identity_verification.repository.verification_log_repository import (
    VerificationLogRepository,
)
from extensions.identity_verification.router.identity_verification_requests import (
    OnfidoCallBackVerificationRequestObject,
    OnfidoVerificationResult,
)
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationAdapter
from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class ReceiveOnfidoResultUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        auth_repo: AuthorizationRepository,
        email_verification_adapter: IdentityVerificationEmailAdapter,
        verification_adapter: IdentityVerificationAdapter,
        verification_log_repo: VerificationLogRepository,
    ):
        self._auth_repo = auth_repo
        self._email_verification_result_adapter = email_verification_adapter
        self._onfido_adapter = verification_adapter
        self._user_verification_log_repo = verification_log_repo

    def process_request(self, request_object: OnfidoCallBackVerificationRequestObject):
        check = self._onfido_adapter.retrieve_verification_check(
            request_object.payload.object.id
        )
        check = OnfidoVerificationResult.from_dict(check)

        user = self._auth_repo.retrieve_user(onfidoApplicantId=check.applicant_id)

        if check.status == VerificationLog.StatusType.COMPLETE.value:
            self._set_verification_status_if_complete(check.result, check.applicant_id)
            self._send_notifications_to_user(user)
        else:
            self._auth_repo.update_user_onfido_verification_status(
                applicant_id=check.applicant_id,
                verification_status=User.VerificationStatus.ID_VERIFICATION_IN_PROCESS,
            )
        self._save_user_verification_to_log(
            check.status, check.result, check.id, check.applicant_id, user.id
        )

    def _save_user_verification_to_log(
        self, status: str, result: str, check_id: str, applicant_id: str, user_id: str
    ):
        verification_status = VerificationLog.StatusType(status).name
        verification_result = VerificationLog.ResultType(result).name

        verification_log: VerificationLog = VerificationLog.from_dict(
            {
                VerificationLog.VERIFICATION_STATUS: verification_status,
                VerificationLog.VERIFICATION_RESULT: verification_result,
                VerificationLog.CHECK_ID: check_id,
                VerificationLog.APPLICANT_ID: applicant_id,
                VerificationLog.USER_ID: user_id,
            }
        )
        self._user_verification_log_repo.create_or_update_verification_log(
            verification_log
        )

    def _set_verification_status_if_complete(self, result: str, applicant_id: str):
        if result == VerificationLog.ResultType.CLEAR.value:
            self._auth_repo.update_user_onfido_verification_status(
                applicant_id=applicant_id,
                verification_status=User.VerificationStatus.ID_VERIFICATION_SUCCEEDED,
            )
        else:
            self._auth_repo.update_user_onfido_verification_status(
                applicant_id=applicant_id,
                verification_status=User.VerificationStatus.ID_VERIFICATION_FAILED,
            )

    def _send_notifications_to_user(self, user: User):
        self._send_verification_result_push_notification(user)
        if user.email:
            self._send_verification_result_email(user)

    @staticmethod
    def _get_user_locale(user: User) -> str:
        return AuthorizedUser(user).get_language()

    def _send_verification_result_email(self, user: User):
        self._email_verification_result_adapter.send_verification_result_email(
            to=user.email,
            username=user.get_full_name(),
            locale=self._get_user_locale(user),
        )

    def _send_verification_result_push_notification(self, user: User):
        locale = self._get_user_locale(user)

        action = "VERIFICATION_RESULTS"

        title = i18n.t("VerificationResults.title", locale=locale)
        body = i18n.t("VerificationResults.body", locale=locale)
        notification_template = {"title": title, "body": body}
        prepare_and_send_push_notification(
            user.id, action, notification_template, run_async=True
        )
