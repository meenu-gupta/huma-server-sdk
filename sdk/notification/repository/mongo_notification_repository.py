from datetime import datetime

from mongoengine import ObjectIdField, StringField, DateTimeField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument
from sdk.notification.model.device import Device, PushIdType
from sdk.notification.repository.notification_repository import NotificationRepository


class MongoDeviceDocument(MongoPhoenixDocument):
    meta = {"collection": "device"}

    PUSH_ID_TYPE_CHOICES = [item.value for item in PushIdType]

    userId = ObjectIdField(required=True)
    devicePushId = StringField(required=True)
    devicePushIdType = StringField(required=True, choices=PUSH_ID_TYPE_CHOICES)
    deviceDetails = StringField()
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)


class MongoNotificationRepository(NotificationRepository):
    def register_device(self, device: Device) -> str:
        device_doc = MongoDeviceDocument.objects(
            userId=device.userId, devicePushId=device.devicePushId
        ).first()
        if device_doc:
            return Device.from_dict(device_doc.to_dict()).id

        return str(MongoDeviceDocument(**device.to_dict(include_none=False)).save().id)

    def unregister_device(
        self, user_id: str, device_push_id: str = None, voip_device_push_id: str = None
    ):
        if device_push_id:
            MongoDeviceDocument.objects(
                devicePushId=device_push_id, userId=user_id
            ).delete()
        if voip_device_push_id:
            MongoDeviceDocument.objects(
                devicePushId=voip_device_push_id,
                userId=user_id,
                devicePushIdType=PushIdType.IOS_VOIP.value,
            ).delete()

    def retrieve_devices(self, user_id: str) -> list[Device]:
        options = {}
        options.update({"userId": user_id})

        device_docs = MongoDeviceDocument.objects(**options)
        devices = [Device.from_dict(device_doc.to_dict()) for device_doc in device_docs]
        return devices

    def delete_device(self, device_push_id: str) -> None:
        """
        called when push id not valid anymore
        """
        MongoDeviceDocument.objects(devicePushId=device_push_id).delete()

    def delete_devices(self, ids: list[str]) -> None:
        """
        deletes multiple devices by list of ids
        """
        if not ids:
            return
        MongoDeviceDocument.objects(devicePushId__in=ids).delete()
