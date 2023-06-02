from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, default_field


@convertibleclass
class JwtTokenConfig:
    secret: str = default_field()
    audience: str = field(default="urn:mp:auth")
    algorithm: str = field(default="HS256")
