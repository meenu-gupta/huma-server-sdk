from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from sdk.common.utils.validators import must_be_present


@convertibleclass
class TwilioSmsVerificationConfig:
    sourcePhoneNumber: str = required_field()
    templateKey: str = required_field()
    serviceName: str = required_field()
    useTwilioVerify: bool = field(default=False)
    twilioVerifyServiceSid: str = default_field()
    templateAndroidKey: str = default_field()

    @classmethod
    def validate(cls, conf):
        if conf.useTwilioVerify:
            must_be_present(twilioServiceSid=conf.twilioVerifyServiceSid)
