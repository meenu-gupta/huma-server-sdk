from enum import Enum

from sdk import meta
from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from sdk.common.utils.validators import validate_url_https


@convertibleclass
class Webhook:
    ENDPOINT = "ENDPOINT"

    class WebhookAuthType(Enum):
        NONE = "NONE"
        BASIC = "BASIC"
        BEARER = "BEARER"

    endpoint: str = required_field(metadata=meta(validate_url_https))

    authType: WebhookAuthType = required_field(default=WebhookAuthType.NONE.value)
    username: str = default_field()
    password: str = default_field()
    token: str = default_field()
