import logging

from i18n import t

from sdk.auth.use_case.auth_request_objects import SendVerificationTokenMethod
from sdk.common.adapter.email_adapter import (
    EmailAdapter,
    PercentageTemplate,
    TemplateParameters,
)
from sdk.common.adapter.one_time_password_repository import (
    OneTimePasswordRepository,
    OneTimePassword,
)
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.constants import RTL
from sdk.common.exceptions.exceptions import InvalidEmailConfirmationCodeException
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.common.utils.token.jwt.jwt import IDENTITY_CLAIM_KEY
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig

log = logging.getLogger(__name__)


class EmailConfirmationAdapter:
    CONFIRMATION_CODE_TYPE = "Confirmation"
    RESET_PASSWORD_CODE_TYPE = "ResetPassword"

    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
        token_adapter: TokenAdapter,
        email_adapter: EmailAdapter,
        otp_repo: OneTimePasswordRepository,
    ):
        self._web_app_url = config.server.webAppUrl
        self._not_found_link = config.server.project.notFoundLink
        self._token_adapter = token_adapter
        self._email_adapter = email_adapter
        self._otp_repo = otp_repo

    def send_confirmation_email(
        self,
        to: str,
        username: str,
        client: Client,
        method: SendVerificationTokenMethod,
        locale: str = Language.EN,
    ):
        confirmation_code = self.create_or_retrieve_code_for(
            to, self.CONFIRMATION_CODE_TYPE
        )
        button_link = self._not_found_link
        if method == SendVerificationTokenMethod.EMAIL_SIGNUP_CONFIRMATION:
            if client.deepLinkBaseUrl:
                button_link = f"{client.deepLinkBaseUrl}/register?confirmationCode={confirmation_code}"
        elif method == SendVerificationTokenMethod.EXISTING_USER_EMAIL_CONFIRMATION:
            if client.deepLinkBaseUrl:
                button_link = f"{client.deepLinkBaseUrl}/login?confirmationCode={confirmation_code}"
        else:
            raise NotImplementedError

        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=PercentageTemplate(
                t("EmailVerification.cp.title", locale=locale)
            ).safe_substitute(username=username),
            subtitle=t("ConfirmationEmail.subtitle", locale=locale),
            body=t("ConfirmationEmail.body", locale=locale),
            buttonLink=button_link,
            buttonText=t("ConfirmationEmail.buttonText", locale=locale),
        )
        subject = t("ConfirmationEmail.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def send_reset_password_email(
        self,
        to: str,
        client: Client,
        locale: str = Language.EN,
    ):
        code = self.create_or_retrieve_code_for(to, self.RESET_PASSWORD_CODE_TYPE)
        button_link = self._not_found_link
        if client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/reset-password?code={code}"
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("ResetPassword.subtitle", locale=locale),
            body=t("ResetPassword.body", locale=locale),
            buttonLink=button_link,
            buttonText=t("ResetPassword.buttonText", locale=locale),
        )
        subject = t("ResetPassword.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def verify_code(
        self, code: str, email: str, code_type: str, delete_code: bool = True
    ) -> bool:
        if not self._otp_repo.verify_password(email, code, code_type, delete_code):
            raise InvalidEmailConfirmationCodeException

        decoded_token = self._token_adapter.verify_confirmation_token(code)
        if not decoded_token or decoded_token[IDENTITY_CLAIM_KEY] != email:
            raise InvalidEmailConfirmationCodeException
        return True

    def delete_code(self, code: str, email: str, code_type: str) -> bool:
        self._otp_repo.delete_otp(email, code_type, code)

    def create_or_retrieve_code_for(self, email: str, code_type: str):
        otp = self._otp_repo.retrieve_otp(email, code_type)
        if otp:
            return otp.password

        code = self._token_adapter.create_confirmation_token(email)
        otp = OneTimePassword.from_dict(
            {
                OneTimePassword.IDENTIFIER: email,
                OneTimePassword.PASSWORD: code,
                OneTimePassword.TYPE: code_type,
            }
        )
        self._otp_repo.create_otp(otp)
        return code

    def send_info_email(
        self, translation_placeholder: str, to: str, locale: str = Language.EN
    ):
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t(f"{translation_placeholder}.title", locale=locale),
            body=t(f"{translation_placeholder}.body", locale=locale),
        )
        subject = t(f"{translation_placeholder}.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_info_html(param),
        )

    def send_password_changed_email(self, to: str, locale: str = Language.EN):
        return self.send_info_email("PasswordChangedEmail", to, locale)

    def send_mfa_phone_number_updated_email(self, to: str, locale: str = Language.EN):
        return self.send_info_email("MFAPhoneNumberChanged", to, locale)
