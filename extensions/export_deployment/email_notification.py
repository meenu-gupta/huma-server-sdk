from i18n import t
import logging

from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.adapter.email_adapter import (
    EmailAdapter,
    TemplateParameters,
    PercentageTemplate,
)
from sdk.common.localization.utils import Language
from sdk.common.constants import RTL
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig, Project

logger = logging.getLogger(__name__)


def _compose_params(title, subtitle, body, button_link, button_text, locale):
    return TemplateParameters(
        textDirection=RTL if locale in Language.get_rtl_languages() else "",
        title=t(f"{title}", locale=locale),
        subtitle=t(f"{subtitle}", locale=locale),
        body=t(f"{body}", locale=locale),
        buttonText=t(f"{button_text}", locale=locale),
        buttonLink=button_link,
    )


class EmailUserExportStatusService:
    @autoparams()
    def __init__(
        self,
        email_adapter: EmailAdapter,
        repo: AuthRepository,
        server_config: PhoenixServerConfig,
    ):
        self._email_adapter = email_adapter
        self._repo = repo
        self._server_config = server_config
        self._project: Project = self._server_config.server.project

    def _get_button_link(self, user_id):
        button_link = self._project.notFoundLink
        client = self._get_client(user_id)
        if not client:
            return button_link
        return f"{client.deepLinkBaseUrl}/download-user-data"

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
        device_agent = device_session.deviceAgent
        if device_agent and "iOS" in device_agent:
            client = self._project.get_client_by_client_type(Client.ClientType.USER_IOS)
        elif device_agent and "Android" in device_agent:
            client = self._project.get_client_by_client_type(
                Client.ClientType.USER_ANDROID
            )
        else:
            client = self._project.get_client_by_client_type(Client.ClientType.USER_WEB)
        return client

    def send_success_data_generation_email(
        self,
        user_id: str,
        username: str,
        to: str,
        locale: str,
    ):
        title = PercentageTemplate(
            t("Notification.export.title", locale=locale)
        ).safe_substitute(username=username)
        params = _compose_params(
            title=title,
            subtitle=t("Notification.export.subtitle.success", locale=locale),
            body=t("Notification.export.body.success", locale=locale),
            button_link=self._get_button_link(user_id),
            button_text=t("Notification.export.buttonText.success", locale=locale),
            locale=locale,
        )
        subject = t(f"Notification.export.subject", locale=locale)
        self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_html_with_button(params),
        )

    def send_failure_data_generation_email(
        self,
        user_id: str,
        username: str,
        to: str,
        locale: str,
    ):
        title = PercentageTemplate(
            t("Notification.export.title", locale=locale)
        ).safe_substitute(username=username)
        params = _compose_params(
            title=title,
            subtitle=t("Notification.export.subtitle.error", locale=locale),
            body=t("Notification.export.body.error", locale=locale),
            button_link=self._get_button_link(user_id),
            button_text=t("Notification.export.buttonText.error", locale=locale),
            locale=locale,
        )
        subject = t(f"Notification.export.subject", locale=locale)
        self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_html_with_button(params),
        )
