from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.convertible import required_field, meta, convertibleclass
from sdk.common.utils.validators import validate_email


@convertibleclass
class SetStaticOTPRequestObject(RequestObject):
    email: str = required_field(metadata=meta(validate_email))
