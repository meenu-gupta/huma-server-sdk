from sdk import meta
from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from sdk.common.utils.validators import validate_url_https, validate_json


@convertibleclass
class GCPFhir:
    URL = "URL"
    SERVICE_ACCOUNT_DATA = "serviceAccountData"
    CONFIG_BODY = "configBody"

    url: str = required_field(metadata=meta(validate_url_https))
    serviceAccountData: str = required_field(metadata=meta(validate_json))
    config: dict = default_field()
