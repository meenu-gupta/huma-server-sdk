import abc
from abc import ABC
from dataclasses import field
from typing import Optional, Union

from sdk import convertibleclass
from sdk.common.utils.convertible import default_field


@convertibleclass
class NotificationMessage:
    """
    Banner message appears when app is down
    """

    title: str = default_field()
    body: str = default_field()


@convertibleclass
class AndroidMessage:
    notification: NotificationMessage = default_field()
    data: dict = default_field()
    priority: str = field(default="high")


@convertibleclass
class ApnsMessage:
    """ """

    notification: NotificationMessage = default_field()
    data: dict = default_field()
    priority: int = field(default=10)
    type: str = field(default="alert")
    badge: int = default_field()


@convertibleclass
class VoipApnsMessage(ApnsMessage):
    type: str = field(default="voip")


@convertibleclass
class AliCloudMessage(AndroidMessage):
    pass


class PushAdapter(ABC):
    @abc.abstractmethod
    def send_message_to_identities(
        self,
        identities: list[str],
        message: Union[
            AndroidMessage, ApnsMessage, VoipApnsMessage, AliCloudMessage
        ] = None,
        ttl: Optional[int] = None,
    ) -> list[str]:
        """
        :return A list of expired or invalid tokens
        :note
        Supported fields on android it should be like:
        {
            "notification": { "title": "notification title", "body": "body"}, <= Optional
            "priority": "high", <= Optional
            "data": {  <= Mandatory

            }
        }
        Supported fields on USER_IOS it should be like:
        {
            "aps": { <= Mandatory
                "category": "CALL_CATEGORY", <= Optional
                "alert": {
                    "title": "Video call title - TBD", <= Mandatory
                    "body": "Video call body - TBD", <= Mandatory
                },
                "badge": 1,  <= Optional
                "sound": "default", <= Optional
            },
            "operation": { <= Optional
                "action": "OPEN_VIDEO_CALL",
                "parameters": {"video_call_id": video_call_id},
            }
        }
        """
        raise NotImplementedError
