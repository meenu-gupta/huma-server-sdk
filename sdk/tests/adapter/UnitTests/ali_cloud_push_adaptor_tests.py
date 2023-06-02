import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from aliyunsdkcore.acs_exception.exceptions import ServerException
from freezegun import freeze_time

from sdk.common.adapter.alibaba.ali_cloud_push_adaptor import AliCloudPushAdapter

ALI_CLOUD_PUSH_ADAPTER_PATH = "sdk.common.adapter.alibaba.ali_cloud_push_adaptor"


class AliCloudPushAdapterTestCase(unittest.TestCase):
    @freeze_time("2012-01-14")
    def test_send_message_to_identities(self):
        ali_push_adaptor = AliCloudPushAdapter(config=MagicMock())
        ali_push_adaptor._request = MagicMock()
        ali_push_adaptor._clt = MagicMock()

        push_date = datetime.utcnow()
        expire_date = datetime.utcnow() + timedelta(hours=+24)

        push_time = push_date.strftime("%Y-%m-%dT%XZ")
        expire_time = expire_date.strftime("%Y-%m-%dT%XZ")

        identities = ["one", "two"]
        ali_cloud_message = MagicMock(
            notification=MagicMock(title="Title", body="Message body")
        )

        ali_push_adaptor.send_message_to_identities(
            identities=identities, message=ali_cloud_message
        )

        ali_push_adaptor._request.set_TargetValue.assert_called()
        ali_push_adaptor._request.set_Title.assert_called_with(
            ali_cloud_message.notification.title
        )
        ali_push_adaptor._request.set_Body.assert_called_with(
            ali_cloud_message.notification.body
        )
        ali_push_adaptor._request.set_AndroidPopupTitle.assert_called_with(
            ali_cloud_message.notification.title
        )
        ali_push_adaptor._request.set_AndroidPopupBody.assert_called_with(
            ali_cloud_message.notification.body
        )

        ali_push_adaptor._request.set_PushTime.assert_called_with(push_time)
        ali_push_adaptor._request.set_ExpireTime.assert_called_with(expire_time)
        ali_push_adaptor._request.set_StoreOffline.assert_called()
        ali_push_adaptor._request.set_AndroidExtParameters.assert_called()

        ali_push_adaptor._clt.do_action_with_exception.assert_called_with(
            ali_push_adaptor._request
        )

    @freeze_time("2012-01-14")
    def test_send_message_to_identities_exception(self):
        ali_push_adaptor = AliCloudPushAdapter(config=MagicMock())
        ali_push_adaptor._request = MagicMock()
        ali_push_adaptor._clt = MagicMock()
        identities = ["one", "two"]
        ali_cloud_message = MagicMock(
            notification=MagicMock(title="Title", body="Message body")
        )
        ali_push_adaptor._clt.do_action_with_exception.side_effect = ServerException(
            code=1, http_status=400, msg="Specified DeviceId format is not valid."
        )
        output = ali_push_adaptor.send_message_to_identities(
            identities=identities, message=ali_cloud_message
        )
        assert output == identities

        ali_push_adaptor._clt.do_action_with_exception.side_effect = BaseException()
        output = ali_push_adaptor.send_message_to_identities(
            identities=identities, message=ali_cloud_message
        )
        assert output == []


if __name__ == "__main__":
    unittest.main()
