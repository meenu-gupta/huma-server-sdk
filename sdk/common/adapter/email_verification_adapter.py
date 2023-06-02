from urllib import parse

from i18n import t

from sdk.common.adapter.email_adapter import (
    TemplateParameters,
    PercentageTemplate,
    EmailAdapter,
)
from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.constants import RTL
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import Client
from sdk.phoenix.config.server_config import PhoenixServerConfig


class EmailVerificationAdapter:
    @autoparams()
    def __init__(
        self,
        otp_repo: OneTimePasswordRepository,
        server_config: PhoenixServerConfig,
        email_adapter: EmailAdapter,
    ):
        self._server_config: PhoenixServerConfig = server_config
        self._otp_repo = otp_repo
        self._email_adapter = email_adapter

    def send_verification_email(
        self, to: str, client: Client, username: str, locale: str = Language.EN
    ):
        CT = Client.ClientType
        verification_code = self._otp_repo.generate_or_get_password(to)
        email = parse.quote(to)

        button_link = self._server_config.server.project.notFoundLink
        if client.deepLinkBaseUrl:
            button_link = PercentageTemplate(
                f"{client.deepLinkBaseUrl}/login?email=%email&verificationCode=%verificationCode"
            ).safe_substitute(email=email, verificationCode=verification_code)

        if client.clientType in (CT.USER_IOS, CT.USER_ANDROID, CT.USER_WEB):
            half_len = len(verification_code) // 2
            bold_title = (
                f"{verification_code[:half_len]}-{verification_code[half_len:]}"
            )
            param = TemplateParameters(
                title=t("EmailVerification.mobile.title", locale=locale),
                boldTitle=bold_title,
                body=t("EmailVerification.mobile.body", locale=locale),
                buttonLink=button_link,
                buttonText=t("EmailVerification.mobile.buttonText", locale=locale),
            )
            subject = t("EmailVerification.mobile.subject", locale=locale)
        elif client.clientType in (CT.MANAGER_WEB, CT.ADMIN_WEB):

            param = TemplateParameters(
                title=PercentageTemplate(
                    t("EmailVerification.cp.title", locale=locale)
                ).safe_substitute(username=username),
                body=t("EmailVerification.cp.body", locale=locale),
                buttonLink=button_link,
                buttonText=t("EmailVerification.cp.buttonText", locale=locale),
            )
            subject = t("EmailVerification.cp.subject", locale=locale)
        else:
            raise InvalidRequestException(f"Client {client.clientType} not supported")

        if locale in Language.get_rtl_languages():
            param.textDirection = RTL

        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def verify_code(self, code: str, email: str) -> bool:
        return self._otp_repo.verify_password(email, code)
