from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, default_field


@convertibleclass
class TencentCloudCosConfig:
    secretId: str = default_field()
    secretKey: str = default_field()
    region: str = default_field()
    scheme: str = field(default="https")
    bucket: str = default_field()
