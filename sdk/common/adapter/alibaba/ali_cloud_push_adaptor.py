import logging
from datetime import datetime, timedelta
from typing import Optional

from aliyunsdkcore import client
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkpush.request.v20160801 import PushRequest

from sdk.common.adapter.alibaba.ali_cloud_push_config import AliCloudPushConfig
from sdk.common.adapter.push_notification_adapter import PushAdapter, AliCloudMessage

logger = logging.getLogger(__name__)


class AliCloudPushAdapter(PushAdapter):
    def __init__(self, config: AliCloudPushConfig):
        self._config = config
        self._clt = client.AcsClient(
            ak=self._config.accessKeyId,
            secret=self._config.accessKeySecret,
            region_id=self._config.region,
        )
        self._app_key = self._config.appKey
        self._request = PushRequest.PushRequest()
        self._set_push_request_properties()

    def send_message_to_identities(
        self,
        identities: list[str],
        message: AliCloudMessage = None,
        ttl: Optional[int] = None,
    ) -> list[str]:

        to_be_deleted = []
        if not identities or not message:
            return to_be_deleted
        for identity in identities:
            # Target value separated by ,
            title = message.notification.title
            body = message.notification.body
            self._request.set_TargetValue(identity)
            self._request.set_Title(title)
            self._request.set_Body(body)
            self._request.set_AndroidPopupTitle(title)
            self._request.set_AndroidPopupBody(body)
            # Push time control
            push_date = datetime.utcnow()
            # Offline storage for 24 hours
            expire_date = datetime.utcnow() + timedelta(hours=+24)
            # ISO8601T
            push_time = push_date.strftime("%Y-%m-%dT%XZ")
            expire_time = expire_date.strftime("%Y-%m-%dT%XZ")
            self._request.set_PushTime(push_time)
            self._request.set_ExpireTime(expire_time)
            self._request.set_StoreOffline(True)
            self._request.set_AndroidExtParameters(message.data)

            try:
                self._clt.do_action_with_exception(self._request)
            except ServerException as e:
                if (
                    e.http_status == 400
                    and e.message == "Specified DeviceId format is not valid."
                ):
                    logger.info(f"Deleted invalid DeviceId {identity}.")
                    to_be_deleted.append(identity)
            except BaseException as e:
                logger.warning(f"Alicloud push error for [{identity}] due to [{e}]")

        return to_be_deleted

    def _set_push_request_properties(self):
        self._request.set_AppKey(self._app_key)
        # Push target: DEVICE, ALIAS, ACCOUNT, TAG, ALL
        self._request.set_Target("DEVICE")
        # Device Type ANDROID iOS ALL
        self._request.set_DeviceType("ANDROID")
        # Push type: MESSAGE NOTICE
        self._request.set_PushType("NOTICE")
        # Notify type: VIBRATE, SOUND, BOTH, NONE
        self._request.set_AndroidNotifyType("BOTH")
        # Notification bar type: 1-100
        self._request.set_AndroidNotificationBarType(1)
        # Jump to when clicked push notification: APPLICATION, ACTIVITY, URL, NONE
        self._request.set_AndroidOpenType("ACTIVITY")
        # Activity，only for AndroidOpenType="Activity"
        self._request.set_AndroidActivity("com.medopad.app.aliyun.PopupPushActivity")
        self._request.set_AndroidMusic("default")
        # Third party pop-up window for offline push
        self._request.set_AndroidPopupActivity(
            "com.medopad.app.aliyun.PopupPushActivity"
        )
        # set channel
        self._request.set_AndroidNotificationChannel("aliyun_channel_id")
        self._request.set_StoreOffline(True)
