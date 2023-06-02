from sdk.common.utils.convertible import convertibleclass, required_field, default_field


@convertibleclass
class AliCloudSmsParameters:
    region: str = required_field()
    domain: str = required_field()
    fromId: str = required_field()
    templateCode: str = required_field()


@convertibleclass
class AliCloudSmsConfig:
    accessKeyId: str = default_field()
    accessKeySecret: str = default_field()
    params: AliCloudSmsParameters = default_field()
