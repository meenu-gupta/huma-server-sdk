from typing import Optional

from twilio.rest import Client

from sdk.common.adapter.push_notification_adapter import PushAdapter
from sdk.common.adapter.twilio.twilio_push_config import TwilioPushConfig
from sdk.notification.model.device import Device, PushIdType


class TwilioPushAdapter(PushAdapter):  # pragma: no cover
    """
    how to configure it:
    > twilioPush:
    >   accountSid: !ENV ${MP_TWILIO_ACCOUNT_SID}
    >   serviceSid: !ENV ${MP_TWILIO_SERVICE_SID}
    >   authToken: eENV ${MP_TWILIO_AUTH_TOKEN}
    how to use it:
    > send: TwilioPushAdapter = inject.instance('twilioPushAdapter')
    > send.send_push_to_identities(device, "Hello, world")
    """

    def __init__(self, config: TwilioPushConfig):
        client = Client(config.accountSid, config.authToken)
        self.notify_service = client.notify.services(config.serviceSid)

    def send_push_to_identities(self, identities: list[Device], text: str) -> None:
        """
        :param identities: list of a Device.DEVICE_PUSH_ID (twilio identity id)
        :param text:     Content of a message
        :return: None
        """
        if identities:
            for each in identities:
                if each.devicePushIdType == PushIdType.TWILIO:
                    self.notify_service.notifications.create(
                        identity=each.devicePushId, body=text
                    )

    def send_raw_push_to_identities(
        self,
        identities: list[str],
        raw: dict,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> list[str]:
        pass
