import logging

import i18n
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.adapter.sms_adapter import SmsAdapter
from sdk.common.adapter.sms_verification_adapter import SmsVerificationAdapter
from sdk.common.adapter.twilio.twilio_sms_verification_config import (
    TwilioSmsVerificationConfig,
)
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


class TwilioSmsVerificationAdapter(SmsVerificationAdapter):
    @autoparams()
    def __init__(
        self,
        otp_repo: OneTimePasswordRepository,
        sms_adapter: SmsAdapter,
        config: TwilioSmsVerificationConfig,
        main_config: PhoenixServerConfig,
    ):
        self._otp_repo = otp_repo
        self._sms_adapter = sms_adapter
        self._config = config
        self._sms_config = main_config.server.adapters.twilioSms

    def send_verification_code(
        self,
        phone_number: str,
        channel: str = "sms",
        locale: str = Language.EN,
        sms_retriever_code: str = "",
    ) -> object:
        if not self._config.useTwilioVerify:
            verification_code = self._otp_repo.generate_or_get_password(phone_number)
            if sms_retriever_code:
                template = i18n.t(
                    self._config.templateAndroidKey,
                    verificationCode=verification_code,
                    serviceName=self._config.serviceName,
                    locale=locale,
                    smsRetrieverCode=sms_retriever_code,
                )
            else:
                template = i18n.t(
                    self._config.templateKey,
                    verificationCode=verification_code,
                    serviceName=self._config.serviceName,
                    locale=locale,
                )
            # force encoding
            template = template + " \u200A"
            return self._sms_adapter.send_sms(
                phone_number, template, self._config.sourcePhoneNumber
            )
        else:
            client = Client(self._sms_config.accountSid, self._sms_config.authToken)
            _ = client.verify.services(
                self._config.twilioVerifyServiceSid
            ).verifications.create(to=phone_number, channel="sms", locale=locale)

    def verify_code(self, code: str, phone_number: str) -> bool:
        if not self._config.useTwilioVerify:
            return self._otp_repo.verify_password(phone_number, code)
        else:
            client = Client(self._sms_config.accountSid, self._sms_config.authToken)
            try:
                return (
                    client.verify.services(self._config.twilioVerifyServiceSid)
                    .verification_checks.create(code, phone_number)
                    .valid
                )
            except TwilioRestException as e:
                log.warning(e.msg)
                return False
