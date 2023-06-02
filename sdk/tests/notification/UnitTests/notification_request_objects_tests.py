import unittest

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.notification.model.device import PushIdType
from sdk.notification.router.notification_requests import (
    RegisterDeviceRequestObject,
    UnRegisterDeviceRequestObject,
)


SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"


class RegisterDeviceRequestObjectTestCase(unittest.TestCase):
    @staticmethod
    def _sample_register_device_req_object(**kwargs):
        req_obj_dict = {
            RegisterDeviceRequestObject.DEVICE_PUSH_ID: "111",
            RegisterDeviceRequestObject.DEVICE_PUSH_ID_TYPE: PushIdType.IOS_VOIP.value,
            **kwargs,
        }
        return RegisterDeviceRequestObject.from_dict(req_obj_dict)

    def test_success_all_fields_are_valid(self):
        try:
            self._sample_register_device_req_object()
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_must_not_be_present_fields(self):
        must_not_be_present_fields = {
            RegisterDeviceRequestObject.ID: SAMPLE_VALID_OBJ_ID,
            RegisterDeviceRequestObject.CREATE_DATE_TIME: "2020-01-01T10:00:00Z",
            RegisterDeviceRequestObject.UPDATE_DATE_TIME: "2020-01-01T10:00:00Z",
        }
        for field in must_not_be_present_fields:
            with self.assertRaises(ConvertibleClassValidationError):
                self._sample_register_device_req_object(
                    **{field: must_not_be_present_fields[field]}
                )

    def test_failure_must_be_present_fields_missed(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RegisterDeviceRequestObject.from_dict(
                {
                    RegisterDeviceRequestObject.DEVICE_PUSH_ID_TYPE: PushIdType.IOS_VOIP.value
                }
            )

        with self.assertRaises(ConvertibleClassValidationError):
            RegisterDeviceRequestObject.from_dict(
                {RegisterDeviceRequestObject.DEVICE_PUSH_ID: "111"}
            )


class UnregisterDeviceRequestObjectTestCase(unittest.TestCase):
    def test_success_create_unregister_device_req_obj(self):
        try:
            UnRegisterDeviceRequestObject.from_dict(
                {
                    UnRegisterDeviceRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID,
                    UnRegisterDeviceRequestObject.DEVICE_PUSH_ID: SAMPLE_VALID_OBJ_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_required_fields_missed(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UnRegisterDeviceRequestObject.from_dict(
                {UnRegisterDeviceRequestObject.USER_ID: SAMPLE_VALID_OBJ_ID}
            )

        with self.assertRaises(ConvertibleClassValidationError):
            UnRegisterDeviceRequestObject.from_dict(
                {UnRegisterDeviceRequestObject.DEVICE_PUSH_ID: SAMPLE_VALID_OBJ_ID}
            )


if __name__ == "__main__":
    unittest.main()
