from sdk import convertibleclass
from sdk.common.utils.convertible import required_field
from sdk.common.utils.validators import must_not_be_present, must_be_present
from sdk.notification.model.device import Device


@convertibleclass
class RegisterDeviceRequestObject(Device):
    @classmethod
    def validate(cls, device):
        must_not_be_present(
            id=device.id,
            updateDateTime=device.updateDateTime,
            createDateTime=device.createDateTime,
        )

        must_be_present(
            devicePushId=device.devicePushId,
            devicePushIdType=device.devicePushIdType,
        )


@convertibleclass
class UnRegisterDeviceRequestObject:
    USER_ID = "userId"
    DEVICE_PUSH_ID = "devicePushId"

    userId: str = required_field()
    devicePushId: str = required_field()
