from i18n import t
from typing import Optional

from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.adapter.email_adapter import (
    TemplateParameters,
    PercentageTemplate,
    EmailAdapter,
)
from sdk.common.constants import RTL
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig, Project, Client


class UserEmailAdapter:
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
        self._email_adapter: EmailAdapter = email_adapter

    def _extract_device_session(self, user_id: str):
        sessions = self._repo.retrieve_device_sessions_by_user_id(
            user_id=user_id, only_enabled=False
        )
        if sessions:
            return sorted(sessions, key=lambda v: v.updateDateTime, reverse=True)[0]

    def _get_client(self, user_id: str):
        device_session = self._extract_device_session(user_id)
        if not device_session:
            return

        client = None
        device_agent = device_session.deviceAgent
        if device_agent and "iOS" in device_agent:
            client = self._project.get_client_by_client_type(Client.ClientType.USER_IOS)
        elif device_agent and "Android" in device_agent:
            client = self._project.get_client_by_client_type(
                Client.ClientType.USER_ANDROID
            )
        return client

    def send_reactivate_user_email(
        self, user_id: str, to: str, username: str, locale: str
    ):
        context = "ReactivateUser"
        if not (client := self._get_client(user_id)):
            client = self._project.get_client_by_client_type(Client.ClientType.USER_WEB)
        title = PercentageTemplate(
            t(f"{context}.title", locale=locale)
        ).safe_substitute(username=username)

        button_link = self._project.notFoundLink
        if client and client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/login?source=reactivated"

        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=title,
            subtitle=t(f"{context}.subtitle", locale=locale),
            body=t(f"{context}.body", locale=locale),
            buttonText=t(f"{context}.buttonText", locale=locale),
            buttonLink=button_link,
        )
        subject = t(f"{context}.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def send_off_board_user_email(
        self, to: str, locale: str, contact_url: Optional[str]
    ):
        context = "OffBoardUser"
        subject = t(f"{context}.subject", locale=locale)
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t(f"{context}.title", locale=locale),
            body=t(f"{context}.body", locale=locale),
        )
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_info_html(param),
        )
