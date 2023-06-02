from sdk.common.utils.convertible import convertibleclass, default_field


@convertibleclass
class RedisDatabaseConfig:
    url: str = default_field()
