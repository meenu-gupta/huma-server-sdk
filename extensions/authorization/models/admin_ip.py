from dataclasses import field
from enum import Enum

from extensions.common.validators import validate_ip
from sdk.common.utils.convertible import meta, convertibleclass, required_field


@convertibleclass
class AdminIP:
    class Mode(Enum):
        WHITELIST = "WHITELIST"
        BLACKLIST = "BLACKLIST"

    ip: str = required_field(metadata=meta(validate_ip))
    mode: Mode = field(default=Mode.WHITELIST)
