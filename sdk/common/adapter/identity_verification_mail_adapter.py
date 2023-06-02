import logging
from urllib import parse

from i18n import t

from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.adapter.email_adapter import (
    TemplateParameters,
    PercentageTemplate,
    EmailAdapter,
)
from sdk.common.constants import RTL
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig, Project, Client

logger = logging.getLogger(__name__)


class IdentityVerificationEmailAdapter:
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        server_config: PhoenixServerConfig,
        email_adapter: EmailAdapter,
    ):
        self._repo = repo
        self._server_config: PhoenixServerConfig = server_config
        self._project: Project = self._server_config.server.project
        self._email_adapter = email_adapter

    def _get_client(self, client_type: Client.ClientType):
        return self._project.get_client_by_client_type(client_type)

    def _extract_device_session(self, email: str):
        try:
            user_id = str(self._repo.get_user(email=email).id)
            sessions = self._repo.retrieve_device_sessions_by_user_id(
                user_id=user_id, only_enabled=False
            )
            if sessions:
                return sorted(sessions, key=lambda v: v.updateDateTime, reverse=True)[0]
        except Exception as e:
            logger.exception(e)

    def send_verification_result_email(
        self,
        to: str,
        username: str,
        locale: str = Language.EN,
    ):
        quote_to = parse.quote(to)
        client = self._get_client(Client.ClientType.USER_WEB)
        device_session = self._extract_device_session(to)
        if device_session:
            device_agent = device_session.deviceAgent
            if device_agent and device_agent.find("iOS") != -1:
                client = self._get_client(Client.ClientType.USER_IOS)
            elif device_agent and device_agent.find("Android") != -1:
                client = self._get_client(Client.ClientType.USER_ANDROID)

        button_link = self._project.notFoundLink
        if client and client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/idverification?email={quote_to}"
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=PercentageTemplate(
                t("VerificationResult.title", locale=locale)
            ).safe_substitute(username=username),
            subtitle=t("VerificationResult.subtitle", locale=locale),
            body=t("VerificationResult.body", locale=locale),
            buttonLink=button_link,
            buttonText=t("VerificationResult.buttonText", locale=locale),
        )
        subject = t("VerificationResult.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )
