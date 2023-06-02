from sdk.common.utils.convertible import convertibleclass, meta, default_field


@convertibleclass
class AliCloudPushConfig:
    accessKeyId: str = default_field()
    accessKeySecret: str = default_field()
    region: str = default_field()
    appKey: str = default_field()
