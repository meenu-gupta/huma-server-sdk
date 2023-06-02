from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import (
    validate_rate_limit,
    validate_rate_limit_strategy,
)


@convertibleclass
class LimiterConfig:
    enable: bool = field(default=True)
    default: str = default_field(metadata=meta(validate_rate_limit))


@convertibleclass
class ServerLimiterConfig(LimiterConfig):
    storageUri: str = default_field()
    strategy: str = field(
        default="fixed-window", metadata=meta(validate_rate_limit_strategy)
    )


@convertibleclass
class AuthLimiterConfig(LimiterConfig):
    signup: str = default_field(metadata=meta(validate_rate_limit))
    checkAuthAttributes: str = default_field(metadata=meta(validate_rate_limit))


@convertibleclass
class StorageLimiterConfig(LimiterConfig):
    read: str = default_field(metadata=meta(validate_rate_limit))
    write: str = default_field(metadata=meta(validate_rate_limit))
