import logging
import time
from typing import Optional, Union

from gobiko.apns.exceptions import BadDeviceToken, PartialBulkMessage

from sdk.common.adapter.apns.apns_push_config import APNSPushConfig
from sdk.common.adapter.push_notification_adapter import (
    PushAdapter,
    ApnsMessage,
    VoipApnsMessage,
)

from gobiko.apns import APNsClient

from sdk.common.utils.validators import remove_none_values

logger = logging.getLogger(__name__)


class APNSPushAdapter(PushAdapter):
    """
    how to configure it:
    > apnsPush:
    >   teamId: "something"
    >   bundleId: "something"
    >   apnsKey: "key"
    >   apnsKeyId: "adf121"
    >   useSandbox: true

    how to use it:
    > send: APNSPushAdapter = inject.instance('apnsPushAdapter')
    > send.send_push_to_identities(device_str, "Hello, world")
    """

    def __init__(self, config: APNSPushConfig):
        self.apns_client = APNsClient(
            team_id=config.teamId,
            bundle_id=config.bundleId,
            auth_key_id=config.authKeyId,
            auth_key_filepath=config.authKeyFilePath,
            use_sandbox=config.useSandbox,
        )

    def send_message_to_identities(
        self,
        identities: list[str],
        message: Union[ApnsMessage, VoipApnsMessage] = None,
        ttl: Optional[int] = None,
    ) -> list[str]:
        """ """
        if not (identities and message):
            return []
        arguments = {
            "alert": {
                "title": message.notification.title,
                "body": message.notification.body,
            },
            "extra": message.data,
            "expiration": int(time.time()) + ttl if ttl else None,
            "priority": message.priority,
            "push_type": message.type,
        }
        if hasattr(message, "badge") and message.badge is not None:
            arguments["badge"] = message.badge
        if message.type == "voip":
            arguments["topic"] = self.apns_client.bundle_id + ".voip"

        if len(identities) == 1:
            try:
                self.apns_client.send_message(
                    identities[0], **remove_none_values(arguments)
                )
                return []
            except BadDeviceToken as e:
                logger.debug(f"APNS single message exception [{str(e)}]")
                return identities

        return self.send_in_bulk_wrapper(identities, remove_none_values(arguments))

    def send_in_bulk_wrapper(self, identities, alert) -> list:
        try:
            self.apns_client.send_bulk_message(identities, alert)
            return []
        except BadDeviceToken:
            logger.info("None of the registration ids were accepted")
            return identities
        except PartialBulkMessage as e:
            logger.debug(f"APNS Bulk message exception [{str(e)}]")
            return e.bad_registration_ids
