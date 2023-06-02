from dataclasses import field
from enum import Enum

from sdk.common.utils.convertible import (
    required_field,
    convertibleclass,
    meta,
    default_field,
)
from sdk.common.utils.validators import validate_range


@convertibleclass
class SentryConfig:
    DSN = "dsn"
    REQUEST_BODIES = "requestBodies"
    TRACES_SAMPLE_RATE = "tracesSampleRate"
    ENVIRONMENT = "environment"
    RELEASE = "release"
    EXTRA_TAGS = "extraTags"

    class RequestBody(Enum):
        never = "never"
        small = "small"
        medium = "medium"
        always = "always"

    enable: bool = field(default=True)
    dsn: str = required_field()
    requestBodies: RequestBody = field(default=RequestBody.always)
    tracesSampleRate: float = field(
        default=1.0, metadata=meta(validate_range(0, 1), value_to_field=float)
    )
    environment: str = field(default="localhost")
    release: str = default_field()
    extraTags: dict = default_field()
