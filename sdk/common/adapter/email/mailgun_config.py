from dataclasses import field

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_email


@convertibleclass
class MailgunConfig:
    domainUrl: str = required_field()
    mailgunApiUrlTemplate: str = field(
        default="https://api.mailgun.net/v3/{0}/messages"
    )
    apiKey: str = required_field()
    defaultFromEmail: str = default_field(metadata=meta(validate_email))
