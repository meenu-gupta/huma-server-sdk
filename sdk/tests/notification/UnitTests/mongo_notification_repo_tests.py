import unittest
from unittest.mock import patch, MagicMock

from sdk.notification.repository.mongo_notification_repository import (
    MongoNotificationRepository,
)

NOTIFICATION_REPO_PATH = "sdk.notification.repository.mongo_notification_repository"
SAMPLE_ID = "600a8476a961574fb38157d5"


class MongoNotificationRepositoryTestCase(unittest.TestCase):
    @patch(f"{NOTIFICATION_REPO_PATH}.MongoDeviceDocument")
    @patch(f"{NOTIFICATION_REPO_PATH}.Device")
    def test_success_register_device(self, device, mongo_doc):
        repo = MongoNotificationRepository()
        device = MagicMock()
        repo.register_device(device)
        mongo_doc.objects.assert_called_with(
            userId=device.userId, devicePushId=device.devicePushId
        )

    @patch(f"{NOTIFICATION_REPO_PATH}.MongoDeviceDocument")
    def test_success_unregister_device(self, mongo_doc):
        repo = MongoNotificationRepository()
        user_id = SAMPLE_ID
        device_push_id = SAMPLE_ID
        repo.unregister_device(user_id, device_push_id)
        mongo_doc.objects.assert_called_with(
            userId=user_id, devicePushId=device_push_id
        )
        mongo_doc.objects(devicePushId=device_push_id).delete.assert_called_once()

    @patch(f"{NOTIFICATION_REPO_PATH}.MongoDeviceDocument")
    @patch(f"{NOTIFICATION_REPO_PATH}.Device")
    def test_success_retrieve_devices(self, device, mongo_doc):
        repo = MongoNotificationRepository()
        user_id = SAMPLE_ID
        repo.retrieve_devices(user_id)
        mongo_doc.objects.assert_called_with(userId=user_id)

    @patch(f"{NOTIFICATION_REPO_PATH}.MongoDeviceDocument")
    def test_success_delete_device(self, mongo_doc):
        repo = MongoNotificationRepository()
        device_push_id = SAMPLE_ID
        repo.delete_device(device_push_id)
        mongo_doc.objects.assert_called_with(devicePushId=device_push_id)
        mongo_doc.objects(devicePushId=device_push_id).delete.assert_called_once()

    @patch(f"{NOTIFICATION_REPO_PATH}.MongoDeviceDocument")
    def test_success_delete_devices(self, mongo_doc):
        repo = MongoNotificationRepository()
        devices_ids = [SAMPLE_ID, SAMPLE_ID]
        repo.delete_devices(devices_ids)
        mongo_doc.objects.assert_called_with(devicePushId__in=devices_ids)
        mongo_doc.objects(devicePushId__in=devices_ids).delete.assert_called_once()


if __name__ == "__main__":
    unittest.main()
