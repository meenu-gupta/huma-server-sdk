import logging
from urllib import parse

from i18n import t

from extensions.authorization.models.role.default_roles import DefaultRoles
from sdk.common.adapter.email_adapter import (
    EmailAdapter,
    TemplateParameters,
    PercentageTemplate,
)
from sdk.common.constants import RTL
from sdk.common.localization.utils import Language
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig

logger = logging.getLogger(__name__)


class EmailInvitationAdapter:
    @autoparams()
    def __init__(
        self,
        server_config: PhoenixServerConfig,
        email_adapter: EmailAdapter,
        default_roles: DefaultRoles,
    ):
        self._domain = server_config.server.webAppUrl
        self._config = server_config
        self._email_adapter = email_adapter
        self._default_roles = default_roles
        self._not_found_link = self._config.server.project.notFoundLink

    def send_invitation_email(
        self,
        to: str,
        role: str,
        client: Client,
        locale: str,
        invitation_code: str,
        sender: str,
    ):
        role_repr = self._default_roles.get_role_repr(role)
        sender = f"<b>{sender}</b>" if sender else "Huma"
        body = PercentageTemplate(
            t("InviteEmail.cp.body.default", locale=locale)
        ).safe_substitute(sender=sender, role=role_repr)
        if role not in self._default_roles:
            body = PercentageTemplate(
                t("InviteEmail.cp.body.custom", locale=locale)
            ).safe_substitute(sender=sender, role=role_repr)
        button_link = self._not_found_link
        if client.deepLinkBaseUrl:
            button_link = (
                f"{client.deepLinkBaseUrl}/register?invitationCode={invitation_code}"
            )
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=t("InviteEmail.cp.title", locale=locale),
            subtitle=t("InviteEmail.cp.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            buttonText=t("InviteEmail.cp.buttonText", locale=locale),
        )
        subject = t("InviteEmail.cp.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def send_user_invitation_email(
        self,
        to: str,
        client: Client,
        locale: str,
        invitation_code: str,
    ):
        email = parse.quote(to)
        body = t("InviteEmail.user.body", locale=locale)
        button_link = not_found_link = self._not_found_link
        if client.deepLinkBaseUrl:
            button_link = PercentageTemplate(
                f"{client.deepLinkBaseUrl}/signup?email=%email&invitationCode=%invitationCode"
            ).safe_substitute(email=email, invitationCode=invitation_code)

        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("InviteEmail.user.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            androidAppLink=self._config.server.androidAppUrl or not_found_link,
            iosAppLink=self._config.server.iosAppUrl or not_found_link,
            firstBlockText=t("InviteEmail.user.firstBlockText", locale=locale),
            secondBlockText=t("InviteEmail.user.secondBlockText", locale=locale),
            buttonText=t("InviteEmail.user.buttonText", locale=locale),
        )
        subject = t("InviteEmail.user.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_email_with_app_downloading(param),
        )

    def send_role_update_email(
        self,
        to: str,
        client: Client,
        locale: str,
        sender: str,
        deployment_count: int,
    ) -> None:
        sender = f"<b>{sender}</b>" if sender else "Huma"
        access_entity = t("UpdateRole.cp.deployment")
        body = PercentageTemplate(
            t("UpdateRole.cp.body", locale=locale)
        ).safe_substitute(
            sender=sender,
            accessEntity=access_entity,
            accessEntityCount=str(deployment_count),
        )
        button_link = self._not_found_link
        if client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}"
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=t("UpdateRole.cp.title", locale=locale),
            subtitle=t("UpdateRole.cp.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            buttonText=t("UpdateRole.cp.buttonText", locale=locale),
        )

        subject = t("UpdateRole.cp.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )

    def send_proxy_role_linked(self, to: str, locale: str):
        body = PercentageTemplate(
            t("ProxyLinkedEmail.body", locale=locale)
        ).safe_substitute()

        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("ProxyLinkedEmail.subtitle", locale=locale),
            body=body,
        )
        subject = t("ProxyLinkedEmail.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_info_html(param),
        )

    def send_assign_new_roles_email(
        self,
        to: str,
        client: Client,
        locale: str,
        sender: str,
        new_role: str,
        old_role: str,
    ):
        sender = f"<b>{sender}</b>" if sender else "Huma"
        body = PercentageTemplate(
            t("AssignNewRole.cp.body", locale=locale)
        ).safe_substitute(sender=sender, newRole=new_role, oldRole=old_role)
        button_link = self._not_found_link
        if client and client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/login"
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("AssignNewRole.cp.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            buttonText=t("AssignNewRole.cp.buttonText", locale=locale),
        )
        subject = t("AssignNewRole.cp.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_html_with_button(param),
        )

    def send_assign_new_multi_resource_role(
        self,
        to: str,
        client: Client,
        locale: str,
        sender: str,
        new_role: str,
        deployment_name: str,
    ):
        sender = f"<b>{sender}</b>" if sender else "Huma"
        body = PercentageTemplate(
            t("AssignNewMultiResourceRole.cp.body", locale=locale)
        ).safe_substitute(
            sender=sender, newRole=new_role, deploymentName=deployment_name
        )
        button_link = self._not_found_link
        if client and client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/login"
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("AssignNewMultiResourceRole.cp.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            buttonText=t("AssignNewMultiResourceRole.cp.buttonText", locale=locale),
        )
        subject = t("AssignNewMultiResourceRole.cp.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_html_with_button(param),
        )

    def send_proxy_invitation_email(
        self,
        to: str,
        locale: str,
        client,
        invitation_code: str,
        sender: str,
        dependant: str,
    ):
        body = PercentageTemplate(
            t("InviteEmail.proxy.body", locale=locale)
        ).safe_substitute(sender=sender, dependant=dependant, email=to)

        button_link = not_found_link = self._not_found_link
        if client and client.deepLinkBaseUrl:
            button_link = f"{client.deepLinkBaseUrl}/register?invitationCode={invitation_code}&email={parse.quote(to)}"

        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            subtitle=t("InviteEmail.proxy.subtitle", locale=locale),
            body=body,
            buttonText=t("InviteEmail.proxy.buttonText", locale=locale),
            buttonLink=button_link,
            androidAppLink=self._config.server.androidAppUrl or not_found_link,
            iosAppLink=self._config.server.iosAppUrl or not_found_link,
            firstBlockText=t("InviteEmail.proxy.firstBlockText", locale=locale),
            secondBlockText=t("InviteEmail.proxy.secondBlockText", locale=locale),
        )

        subject = t("InviteEmail.proxy.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_email_with_app_downloading(param),
        )

    def send_admin_invitation_email(
        self,
        to: str,
        role: str,
        client: Client,
        locale: str,
        invitation_code: str,
        sender: str,
        organization_name: str = None,
    ):
        role_repr = self._default_roles.get_role_repr(role)
        sender = f"<b>{sender}</b>" if sender else "Huma"
        if organization_name:
            body = PercentageTemplate(
                t("InviteEmail.admin.body.organization", locale=locale)
            ).safe_substitute(
                sender=sender, role=role_repr, organization_name=organization_name
            )
        else:
            body = PercentageTemplate(
                t("InviteEmail.admin.body.default", locale=locale)
            ).safe_substitute(sender=sender, role=role_repr)

        button_link = self._not_found_link
        if client.deepLinkBaseUrl:
            button_link = (
                f"{client.deepLinkBaseUrl}/register?invitationCode={invitation_code}"
            )
        param = TemplateParameters(
            textDirection=RTL if locale in Language.get_rtl_languages() else "",
            title=t("InviteEmail.admin.title", locale=locale),
            subtitle=t("InviteEmail.admin.subtitle", locale=locale),
            body=body,
            buttonLink=button_link,
            buttonText=t("InviteEmail.admin.buttonText", locale=locale),
        )
        subject = t("InviteEmail.admin.subject", locale=locale)
        return self._email_adapter.send_html_email(
            from_=self._email_adapter.default_from_email(),
            to=to,
            subject=subject,
            html=self._email_adapter.generate_support_html_with_button(param),
        )
