from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class FCMPushConfig:
    serviceAccountKeyFilePath: str = required_field()
