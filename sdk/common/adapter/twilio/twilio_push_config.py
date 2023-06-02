from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class TwilioPushConfig:
    accountSid: str = required_field()
    serviceSid: str = required_field()
    authToken: str = required_field()
