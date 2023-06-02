import requests
import logging

from sdk.common.adapter.email.mailgun_config import MailgunConfig
from sdk.common.adapter.email_adapter import EmailAdapter

log = logging.getLogger(__name__)


class MailgunEmailAdapter(EmailAdapter):
    """
    how to configure it through config file:
    > mailgunEmail:
    >   domainUrl: medopad.us
    >   apiKey: !ENV ${MP_MAILGUN_API_KEY}

    how to use it:
    > send: EmailAdapter = inject.instance('mailgunEmailAdapter')
    > send.send_html_email('hey@medopad.us', 'milano.fili@medopad.com', 'this one', 'is test')
    """

    def __init__(self, config: MailgunConfig):
        self._config = config

    def send_html_email(self, from_: str, to: str, subject: str, html: str):
        request_url = self._config.mailgunApiUrlTemplate.format(self._config.domainUrl)
        response = requests.post(
            request_url,
            auth=("api", self._config.apiKey),
            data={"from": from_, "to": to, "subject": subject, "html": html},
        )
        log.debug("Status: {0}".format(response.status_code))
        log.debug("Body:   {0}".format(response.text))

    def default_from_email(self):
        return self._config.defaultFromEmail


class DebugEmailAdapter(EmailAdapter):
    """
    this adapter is just for tests.
    so it will be used when user runs tests without email configuration in config file
    """

    def send_html_email(self, from_: str, to: str, subject: str, html: str):
        log.info(f"Send email was called from {from_} to {to}")

    def default_from_email(self):
        log.info("Requested default email")
        return "test@example.com"
