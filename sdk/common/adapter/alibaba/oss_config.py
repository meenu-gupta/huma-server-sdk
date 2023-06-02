from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class OSSConfig:
    accessKeyId: str = required_field()
    accessKeySecret: str = required_field()
    url: str = required_field()
