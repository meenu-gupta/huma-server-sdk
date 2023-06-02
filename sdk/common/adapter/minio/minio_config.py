from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)


@convertibleclass
class MinioConfig:
    url: str = required_field()
    accessKey: str = required_field()
    secretKey: str = required_field()
    secure: bool = required_field(default=False)
    baseUrl: str = default_field()
    serviceUrl: str = default_field()
