import unittest
from unittest.mock import MagicMock

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from sdk.common.localization.utils import Language

CLIENT = MagicMock()
LOCALE = Language.EN
INVITATION_CODE = "invitation_code"
HTML_TEMPLATE = "some_html_template"
DEFAULT_FROM_EMAIL = "test@huma.com"
DEFAULT_SENDER = "Huma Test"


class EmailInvitationAdapterTestCases(unittest.TestCase):
    def setUp(self) -> None:
        self.server_config = MagicMock()
        self.email_adapter = MagicMock()
        self.default_roles = MagicMock()
        self.invitation_adapter = EmailInvitationAdapter(
            server_config=self.server_config,
            email_adapter=self.email_adapter,
            default_roles=self.default_roles,
        )

        self.email_adapter.default_from_email.return_value = DEFAULT_FROM_EMAIL

    def test_send_invitation_email(self):
        to = "test_cp_user@gmail.com"
        role = "AccessController"
        subject = "InviteEmail.cp.subject"

        self.email_adapter.generate_support_html_with_button.return_value = (
            HTML_TEMPLATE
        )

        self.invitation_adapter.send_invitation_email(
            to, role, CLIENT, LOCALE, INVITATION_CODE, DEFAULT_SENDER
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_user_invitation_email(self):
        to = "test_user@gmail.com"
        subject = "InviteEmail.user.subject"

        self.email_adapter.generate_email_with_app_downloading.return_value = (
            HTML_TEMPLATE
        )

        self.invitation_adapter.send_user_invitation_email(
            to, CLIENT, LOCALE, INVITATION_CODE
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_role_update_email(self):
        to = "test_cp_user@gmail.com"
        subject = "UpdateRole.cp.subject"
        deployment_count = 1

        self.email_adapter.generate_support_html_with_button.return_value = (
            HTML_TEMPLATE
        )

        self.invitation_adapter.send_role_update_email(
            to, CLIENT, LOCALE, DEFAULT_SENDER, deployment_count
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_proxy_role_linked(self):
        to = "test_proxy_user@gmail.com"
        subject = "ProxyLinkedEmail.subject"

        self.email_adapter.generate_info_html.return_value = HTML_TEMPLATE

        self.invitation_adapter.send_proxy_role_linked(to, LOCALE)

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_assign_new_roles_email(self):
        to = "test_cp_user@gmail.com"
        subject = "AssignNewRole.cp.subject"
        old_role = "OrganizationStaff"
        new_role = "AccessController"

        self.email_adapter.generate_html_with_button.return_value = HTML_TEMPLATE

        self.invitation_adapter.send_assign_new_roles_email(
            to, CLIENT, LOCALE, DEFAULT_SENDER, new_role, old_role
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_assign_new_multi_resource_role(self):
        to = "test_cp_user@gmail.com"
        subject = "AssignNewMultiResourceRole.cp.subject"
        new_role = "AccessController"
        deployment_name = "Sample Deployment"

        self.email_adapter.generate_html_with_button.return_value = HTML_TEMPLATE

        self.invitation_adapter.send_assign_new_multi_resource_role(
            to, CLIENT, LOCALE, DEFAULT_SENDER, new_role, deployment_name
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )

    def test_send_proxy_invitation_email(self):
        to = "test_proxy_user@gmail.com"
        subject = "InviteEmail.proxy.subject"
        sender = "John Doe"
        dependant = "some_dependant"

        self.email_adapter.generate_email_with_app_downloading.return_value = (
            HTML_TEMPLATE
        )

        self.invitation_adapter.send_proxy_invitation_email(
            to, LOCALE, CLIENT, INVITATION_CODE, sender, dependant
        )

        self.email_adapter.send_html_email.assert_called_with(
            from_=DEFAULT_FROM_EMAIL, to=to, subject=subject, html=HTML_TEMPLATE
        )
