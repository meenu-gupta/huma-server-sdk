from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class TwilioSmsConfig:
    accountSid: str = required_field()
    authToken: str = required_field()
