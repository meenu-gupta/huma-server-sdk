import logging

from sdk.common.localization.utils import Language
from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.adapter.sms_adapter import SmsAdapter
from sdk.common.adapter.sms_verification_adapter import SmsVerificationAdapter
from sdk.common.utils.inject import autoparams

log = logging.getLogger(__name__)


class AliCloudSmsVerificationAdapter(SmsVerificationAdapter):
    @autoparams()
    def __init__(self, otp_repo: OneTimePasswordRepository, sms_adapter: SmsAdapter):
        self._otp_repo = otp_repo
        self._sms_adapter = sms_adapter

    def send_verification_code(
        self,
        phone_number: str,
        channel: str = "sms",
        locale: str = Language.EN,
        sms_retriever_code: str = "",
    ) -> object:
        verification_code = self._otp_repo.generate_or_get_password(phone_number)
        return self._sms_adapter.send_sms(phone_number, verification_code, "")

    def verify_code(self, code: str, phone_number: str) -> bool:
        return self._otp_repo.verify_password(phone_number, code)
