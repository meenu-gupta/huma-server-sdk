from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, default_field
from sdk.limiter.config.limiter import AuthLimiterConfig


@convertibleclass
class AuthConfig:
    enable: bool = field(default=True)
    enableAuth: bool = field(default=True)
    enableAuthz: bool = field(default=True)

    database: str = default_field()
    rateLimit: AuthLimiterConfig = default_field()
    signedUrlSecret: str = default_field()
