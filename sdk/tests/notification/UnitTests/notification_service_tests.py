import unittest
from unittest.mock import patch, MagicMock

from sdk.notification.model.device import PushIdType
from sdk.notification.services.notification_service import (
    NotificationService,
    async_push_for_user,
    async_push_for_voip_user_task,
)

NOTIFICATION_SERVICE_PATH = "sdk.notification.services.notification_service"
SAMPLE_ID = "600a8476a961574fb38157d5"


class NotificationServiceTestCase(unittest.TestCase):
    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    def test_register_device(self, repo):
        service = NotificationService(repo)
        device = MagicMock()

        service.register_device(device)

        repo.register_device.assert_called_with(device)

    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    def test_unregister_device(self, repo):
        service = NotificationService(repo)
        user_id = SAMPLE_ID
        device_push_id = SAMPLE_ID
        voip_device_push_id = SAMPLE_ID

        service.unregister_device(user_id, device_push_id, voip_device_push_id)

        repo.unregister_device.assert_called_with(
            user_id, device_push_id, voip_device_push_id
        )

    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    def test_retrieve_devices(self, repo):
        service = NotificationService(repo)
        user_id = SAMPLE_ID

        service.retrieve_devices(user_id)

        repo.retrieve_devices.assert_called_with(user_id)

    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.async_push_for_user")
    def test_push_for_user(self, push_for_user, repo):
        service = NotificationService(repo)
        user_id = SAMPLE_ID
        android = MagicMock()
        ios = MagicMock()
        ali_cloud = MagicMock()
        ttl = 64

        service.push_for_user(user_id, android, ios, ali_cloud, ttl)

        push_for_user.delay.assert_called_with(
            user_id, android.to_dict(), ios.to_dict(), ali_cloud.to_dict(), ttl
        )

    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.async_push_for_user")
    def test_push_for_user_not_async(self, push_for_user, repo):
        service = NotificationService(repo)
        user_id = SAMPLE_ID
        android = MagicMock()
        ios = MagicMock()
        ali_cloud = MagicMock()
        ttl = 64

        service.push_for_user(user_id, android, ios, ali_cloud, ttl, False)

        push_for_user.assert_called_with(
            user_id, android.to_dict(), ios.to_dict(), ali_cloud.to_dict(), ttl
        )

    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.NotificationRepository")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.async_push_for_voip_user_task")
    def test_push_for_voip_user(
        self, mock_async_push, repo, mock_android_msg, mock_ios_msg
    ):
        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        service = NotificationService(repo)
        user_id = SAMPLE_ID
        android = MagicMock()
        ios_voip = MagicMock()
        ttl = 64

        service.push_for_voip_user(user_id, android, ios_voip, ttl)

        mock_async_push.delay.assert_called_with(
            user_id, android.to_dict(), ios_voip.to_dict(), ttl
        )

    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.inject")
    def test_async_push_for_user(
        self,
        mock_inject,
        mock_android_msg,
        mock_ios_msg,
    ):
        android_device = MagicMock(devicePushIdType=PushIdType.ANDROID_FCM)
        ios_device = MagicMock(devicePushIdType=PushIdType.IOS_APNS)
        ali_cloud_device = MagicMock(devicePushIdType=PushIdType.ALI_CLOUD)

        mock_inject.instance().retrieve_devices.return_value = [
            android_device,
            ios_device,
            ali_cloud_device,
        ]

        mock_inject.instance().send_message_to_identities.return_value = SAMPLE_ID

        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        user_id = SAMPLE_ID
        android_dict = MagicMock()
        ios_dict = MagicMock()
        ali_cloud_dict = MagicMock()
        ttl = 64

        async_push_for_user(user_id, android_dict, ios_dict, ali_cloud_dict, ttl)

        mock_inject.instance().send_message_to_identities.assert_called()
        mock_inject.instance().delete_devices.assert_called()

    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.inject")
    def test_async_push_for_user_ids_falsy(
        self,
        mock_inject,
        mock_android_msg,
        mock_ios_msg,
    ):
        android_device = MagicMock(devicePushIdType=PushIdType.ANDROID_FCM)
        ios_device = MagicMock(devicePushIdType=PushIdType.IOS_APNS)
        ali_cloud_device = MagicMock(devicePushIdType=PushIdType.ALI_CLOUD)

        mock_inject.instance().retrieve_devices.return_value = [
            android_device,
            ios_device,
            ali_cloud_device,
        ]

        mock_inject.instance().send_message_to_identities.return_value = []

        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        user_id = SAMPLE_ID
        android_dict = MagicMock()
        ios_dict = MagicMock()
        ali_cloud_dict = MagicMock()
        ttl = 64

        async_push_for_user(user_id, android_dict, ios_dict, ali_cloud_dict, ttl)

        mock_inject.instance().send_message_to_identities.assert_called()
        assert mock_inject.instance().delete_devices.call_count == 0

    @patch(f"{NOTIFICATION_SERVICE_PATH}.logger")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.inject")
    def test_async_push_for_user_exception(
        self, mock_inject, mock_android_msg, mock_ios_msg, mock_logger
    ):
        android_device = MagicMock(devicePushIdType=PushIdType.ANDROID_FCM)
        ios_device = MagicMock(devicePushIdType=PushIdType.IOS_APNS)
        ali_cloud_device = MagicMock(devicePushIdType=PushIdType.ALI_CLOUD)

        mock_inject.instance().retrieve_devices.return_value = [
            android_device,
            ios_device,
            ali_cloud_device,
        ]

        mock_inject.instance().send_message_to_identities.side_effect = Exception()

        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        user_id = SAMPLE_ID
        android_dict = MagicMock()
        ios_dict = MagicMock()
        ali_cloud_dict = None
        ttl = 64

        async_push_for_user(user_id, android_dict, ios_dict, ali_cloud_dict, ttl)
        mock_logger.warning.assert_called()

    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.inject")
    def test_async_push_for_voip_user_task(
        self,
        mock_inject,
        mock_android_msg,
        mock_ios_msg,
    ):
        android_device = MagicMock(devicePushIdType=PushIdType.ANDROID_FCM)
        ios_device = MagicMock(devicePushIdType=PushIdType.IOS_VOIP)

        mock_inject.instance().retrieve_devices.return_value = [
            android_device,
            ios_device,
        ]

        mock_inject.instance().send_message_to_identities.return_value = SAMPLE_ID

        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        user_id = SAMPLE_ID
        android_dict = MagicMock()
        ios_dict = MagicMock()
        ttl = 64

        async_push_for_voip_user_task(user_id, android_dict, ios_dict, ttl)

        mock_inject.instance().send_message_to_identities.assert_called()
        mock_inject.instance().delete_devices.assert_called()

    @patch(f"{NOTIFICATION_SERVICE_PATH}.logger")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.VoipApnsMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.AndroidMessage")
    @patch(f"{NOTIFICATION_SERVICE_PATH}.inject")
    def test_async_push_for_voip_user_task_exception(
        self, mock_inject, mock_android_msg, mock_ios_msg, mock_logger
    ):
        android_device = MagicMock(devicePushIdType=PushIdType.ANDROID_FCM)
        ios_device = MagicMock(devicePushIdType=PushIdType.IOS_VOIP)

        mock_inject.instance().retrieve_devices.return_value = [
            android_device,
            ios_device,
        ]

        mock_inject.instance().send_message_to_identities.side_effect = Exception()

        mock_android_msg.to_dict.return_value = MagicMock()
        mock_ios_msg.to_dict.return_value = MagicMock()

        user_id = SAMPLE_ID
        android_dict = MagicMock()
        ios_dict = MagicMock()
        ttl = 64

        async_push_for_voip_user_task(user_id, android_dict, ios_dict, ttl)

        mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main()
