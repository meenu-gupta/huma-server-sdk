import logging
from typing import Optional, Union

from sdk.common.adapter.push_notification_adapter import (
    PushAdapter,
    AndroidMessage,
    ApnsMessage,
    VoipApnsMessage,
    AliCloudMessage,
)

logger = logging.getLogger(__name__)


class MockedPushAdapter(PushAdapter):
    def __init__(self):
        pass

    def send_message_to_identities(
        self,
        identities: list[str],
        message: Union[
            AndroidMessage, ApnsMessage, VoipApnsMessage, AliCloudMessage
        ] = None,
        ttl: Optional[int] = None,
    ) -> list[str]:

        if message:
            logger.info(
                f"Mock sending message to identities: {identities} with notification: {message.notification} with data: {message.data} "
            )

        return []
