import logging
from datetime import timedelta
from typing import Optional

import firebase_admin
from firebase_admin import messaging
from firebase_admin.credentials import Certificate
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import AndroidConfig

from sdk.common.adapter.push_notification_adapter import (
    PushAdapter,
    AndroidMessage,
)
from sdk.common.adapter.fcm.fcm_push_config import FCMPushConfig

logger = logging.getLogger(__name__)


class FCMPushAdapter(PushAdapter):
    """
    how to configure it:
    > fcmPush:
    >   apiKey: !ENV ${MP_FCM_ACCOUNT_SID}

    how to use it:
    > send: FCMPushAdapter = inject.instance('fcmPushAdapter')
    > send.send_push_to_identities(device, "Hello, world")
    """

    def __init__(self, config: FCMPushConfig):
        credentials = Certificate(config.serviceAccountKeyFilePath)
        firebase_admin.initialize_app(credential=credentials)

    def send_message_to_identities(
        self,
        identities: list[str],
        message: AndroidMessage = None,
        ttl: Optional[int] = None,
    ) -> list[str]:
        """ """
        if not (identities and message):
            return []
        if len(identities) == 1:
            try:
                msg_to_send = FCMPushAdapter._build_message(identities[0], message, ttl)
                _ = messaging.send(msg_to_send)
                return []
            except FirebaseError as e:
                if e.http_response.status_code in [400, 404]:
                    return identities
                raise e
        else:
            try:
                messages = []
                for identity in identities:
                    msg_to_send = FCMPushAdapter._build_message(identity, message, ttl)
                    messages.append(msg_to_send)

                batch_rsp = messaging.send_all(messages)

                i = 0
                failed_ids = []
                for rsp in batch_rsp.responses:
                    if rsp.exception:
                        if rsp.exception.http_response.status_code in [404, 400]:
                            logger.debug(f"FCM single message failed [{identities[i]}]")
                            failed_ids.append(identities[i])
                        else:
                            logger.warning(
                                f"failed fcm batch send: {identities[i]} due to [{rsp.exception}]"
                            )

                    i += 1
                return failed_ids

            except FirebaseError as e:
                logger.debug(f"FCM single message exception [{str(e)}]")
                raise e

    @staticmethod
    def _build_message(
        identity: str,
        android: AndroidMessage = None,
        ttl: Optional[int] = None,
    ):
        ttl = timedelta(seconds=ttl) if ttl else None
        return messaging.Message(
            notification=messaging.Notification(
                title=android.notification.title, body=android.notification.body
            )
            if android.notification
            else None,
            token=identity,
            data=android.data if android.data else None,
            android=AndroidConfig(priority=android.priority, ttl=ttl),
        )
