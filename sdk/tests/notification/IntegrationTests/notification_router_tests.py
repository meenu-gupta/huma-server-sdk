import unittest
from pathlib import Path

from sdk.auth.component import AuthComponent
from sdk.notification.component import NotificationComponent
from sdk.tests.application_test_utils.comparator import skip
from sdk.tests.test_case import SdkTestCase

USER_ID_1 = "5e8f0c74b50aa9656c34789a"
USER_ID_2 = "5e84b0dab8dfa268b1180536"

DEVICE_TYPE_ANDROID = "ANDROID_FCM"
DEVICE_TYPE_IOS = "IOS_APNS"

DEVICE_ID_1 = "DEV_ID:1"
DEVICE_ID_2 = "DEV_ID:2"
DEVICE_ID_3 = "DEV_ID:3"
DEVICE_ID_4 = "DEV_ID:4"
DEVICE_ID_5 = "DEV_ID:5"

DEVICE_PUSH_ID_1 = "TEST_DEVICE_PUSH_ID_1"
DEVICE_PUSH_ID_2 = "TEST_DEVICE_PUSH_ID_2"
DEVICE_PUSH_ID_3 = "TEST_DEVICE_PUSH_ID_3"
DEVICE_PUSH_ID_4 = "TEST_DEVICE_PUSH_ID_4"
DEVICE_PUSH_ID_5 = "TEST_DEVICE_PUSH_ID_5"


class NotificationTestCase(SdkTestCase):
    components = [AuthComponent(), NotificationComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/users_dump.json")]

    def _model_register_device_request(
        self, device_id: str, device_push_id: str, device_type: str
    ):
        return {
            "devicePushId": device_push_id,
            "devicePushIdType": device_type,
        }

    def _model_register_device_response(self, id: str):
        return {"id": id}

    def _model_get_user_devices_response(self, content):
        return {"items": content, "total": len(content)}

    def _model_get_user_devices_response_internal(self, content):
        return {"items": content, "total": len(content)}

    def _get_user_devices(self, identity):
        rsp = self.flask_client.get(
            f"/api/notification/v1beta/device",
            headers=self.get_headers_for_token(identity=identity),
        )
        self.assertEqual(rsp.status_code, 200)
        return rsp.json

    def _register_user_devices(self, body, identity):
        rsp = self.flask_client.post(
            "/api/notification/v1beta/device/register",
            headers=self.get_headers_for_token(identity),
            json=body,
        )
        self.assertEqual(rsp.status_code, 201)
        return rsp.json

    def test_push_notifications_flow(self):
        rsp = self._get_user_devices(USER_ID_1)
        self.assertDictEqual(rsp, self._model_get_user_devices_response([]))

        rsp = self._get_user_devices(USER_ID_2)
        self.assertDictEqual(rsp, self._model_get_user_devices_response([]))

        device1user1 = self._model_register_device_request(
            DEVICE_ID_1, DEVICE_PUSH_ID_1, DEVICE_TYPE_ANDROID
        )
        device2user1 = self._model_register_device_request(
            DEVICE_ID_2, DEVICE_PUSH_ID_2, DEVICE_TYPE_ANDROID
        )
        device3user1 = self._model_register_device_request(
            DEVICE_ID_3, DEVICE_PUSH_ID_3, DEVICE_TYPE_IOS
        )

        self.assert_matches(
            {"id": skip}, self._register_user_devices(device1user1, USER_ID_1)
        )
        self.assert_matches(
            {"id": skip}, self._register_user_devices(device2user1, USER_ID_1)
        )
        self.assert_matches(
            {"id": skip}, self._register_user_devices(device3user1, USER_ID_1)
        )

        device4user2 = self._model_register_device_request(
            DEVICE_ID_4, DEVICE_PUSH_ID_4, DEVICE_TYPE_ANDROID
        )
        device5user2 = self._model_register_device_request(
            DEVICE_ID_5, DEVICE_PUSH_ID_5, DEVICE_TYPE_IOS
        )

        self.assert_matches(
            {"id": skip}, self._register_user_devices(device4user2, USER_ID_2)
        )
        self.assert_matches(
            {"id": skip}, self._register_user_devices(device5user2, USER_ID_2)
        )

        ignored = {"id": skip, "createDateTime": skip, "updateDateTime": skip}
        self.assert_matches(
            {
                "items": [
                    {**device1user1, **ignored},
                    {**device2user1, **ignored},
                    {**device3user1, **ignored},
                ],
                "total": 3,
            },
            self._get_user_devices(USER_ID_1),
        )

        self.assert_matches(
            {
                "items": [
                    {**device4user2, **ignored},
                    {**device5user2, **ignored},
                ],
                "total": 2,
            },
            self._get_user_devices(USER_ID_2),
        )


if __name__ == "__main__":
    unittest.main()
