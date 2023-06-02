from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from sdk.common.adapter.sms_adapter import SmsAdapter
from sdk.common.adapter.twilio.twilio_sms_config import TwilioSmsConfig
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    InvalidPhoneNumberException,
)

TWILIO_INVALID_PHONE_NUMBER_CODE = 21614
TWILIO_INVALID_FROM_PHONE_NUMBER = 21606


class TwilioSmsAdapter(SmsAdapter):
    """
    how to configure it:
    > twilioSms:
    >   accountSid: !ENV ${MP_TWILIO_ACCOUNT_SID}
    >   authToken: !ENV ${MP_TWILIO_AUTH_TOKEN}
    how to use it:
    > send: SmsAdapter = inject.instance('twilioSmsAdapter')
    > send.send_sms("+447484889827", "test", "")
    """

    def __init__(self, config: TwilioSmsConfig):
        self._config = config

    def send_sms(
        self, phone_number: str, text: str, phone_number_source: str
    ) -> object:
        client = Client(self._config.accountSid, self._config.authToken)
        try:
            message = client.messages.create(
                body=text, from_=phone_number_source, to=phone_number
            )
        except TwilioRestException as e:
            if e.code == TWILIO_INVALID_PHONE_NUMBER_CODE:
                raise InvalidPhoneNumberException
            else:
                raise InvalidRequestException(f"Twilio sending sms error: {e.code}")
        except Exception as e:
            raise InvalidRequestException(f"Twilio sending sms exception: {e}")
        return message.sid
