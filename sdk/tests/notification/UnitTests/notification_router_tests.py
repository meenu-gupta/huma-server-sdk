import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from sdk.common.adapter.push_notification_adapter import (
    VoipApnsMessage,
    NotificationMessage,
    AndroidMessage,
    ApnsMessage,
)
from sdk.notification.model.device import PushIdType
from sdk.notification.router.notification_requests import (
    UnRegisterDeviceRequestObject,
    RegisterDeviceRequestObject,
)
from sdk.notification.router.notification_router import (
    send_notification_call,
    send_notification,
    get_user_devices,
    unregister_device,
    register_device,
)

NOTIFICATION_ROUTER_PATH = "sdk.notification.router.notification_router"
NOTIFICATION_UTILS_PATH = "sdk.common.push_notifications.push_notifications_utils"

testapp = Flask(__name__)
testapp.app_context().push()


class NotificationRouterTestCase(unittest.TestCase):
    @patch(f"{NOTIFICATION_UTILS_PATH}.NotificationService")
    @patch(f"{NOTIFICATION_UTILS_PATH}.datetime_now")
    def test_success_send_notification_call(self, dt_now, service):
        payload = {
            "title": "test title",
            "body": "test body",
            "userId": "111",
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_notification_call()
            data = {
                "click_action": "Test VOIP Notification",
                "title": "test title",
                "body": "test body",
                "action": "Test VOIP Notification",
                "sentDateTime": dt_now(),
            }
            service().push_for_voip_user.assert_called_with(
                payload["userId"],
                android=AndroidMessage(notification=None, data=data, priority="high"),
                ios_voip=VoipApnsMessage(
                    notification=NotificationMessage(
                        title=payload["title"], body=payload["body"]
                    ),
                    data={
                        "action": "Test VOIP Notification",
                        "sentDateTime": dt_now(),
                    },
                    priority=10,
                    type="voip",
                ),
            )

    @patch(f"{NOTIFICATION_UTILS_PATH}.NotificationService")
    @patch(f"{NOTIFICATION_UTILS_PATH}.datetime_now")
    def test_success_send_notification(self, dt_now, service):
        payload = {
            "title": "test title",
            "body": "test body",
            "userId": "111",
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_notification()
            data = {
                "click_action": "Test Notification",
                "title": "test title",
                "body": "test body",
                "action": "Test Notification",
                "sentDateTime": dt_now(),
            }
            service().push_for_user.assert_called_with(
                payload["userId"],
                android=AndroidMessage(
                    notification=None,
                    data=data,
                    priority="high",
                ),
                ios=ApnsMessage(
                    notification=NotificationMessage(
                        title=payload["title"], body=payload["body"]
                    ),
                    data={
                        "operation": {
                            "action": "Test Notification",
                            "sentDateTime": dt_now(),
                        }
                    },
                    priority=10,
                    type="alert",
                ),
                run_async=False,
            )

    @patch(f"{NOTIFICATION_ROUTER_PATH}.NotificationService")
    @patch(f"{NOTIFICATION_ROUTER_PATH}.g")
    def test_success_get_user_devices(self, g_mock, service):
        g_mock.auth_user = MagicMock()
        with testapp.test_request_context("/", method="GET") as _:
            get_user_devices()
            service().retrieve_devices.assert_called_with(g_mock.auth_user.id)

    @patch(f"{NOTIFICATION_ROUTER_PATH}.NotificationService")
    @patch(f"{NOTIFICATION_ROUTER_PATH}.g")
    def test_success_unregister_device(self, g_mock, service):
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.id = "111"
        payload = {UnRegisterDeviceRequestObject.DEVICE_PUSH_ID: "11111"}
        with testapp.test_request_context("/", method="DELETE", json=payload) as _:
            unregister_device()
            service().unregister_device.assert_called_with(
                user_id=g_mock.auth_user.id,
                device_push_id=payload[UnRegisterDeviceRequestObject.DEVICE_PUSH_ID],
            )

    @patch(f"{NOTIFICATION_ROUTER_PATH}.jsonify")
    @patch(f"{NOTIFICATION_ROUTER_PATH}.NotificationService")
    @patch(f"{NOTIFICATION_ROUTER_PATH}.g")
    def test_success_register_device(self, g_mock, service, jsonify):
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.id = "111"
        payload = {
            RegisterDeviceRequestObject.DEVICE_PUSH_ID: "11111",
            RegisterDeviceRequestObject.DEVICE_PUSH_ID_TYPE: PushIdType.IOS_APNS.name,
        }
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            register_device()
            service().register_device.assert_called_with(
                RegisterDeviceRequestObject(
                    id=None,
                    userId=g_mock.auth_user.id,
                    devicePushId=payload[RegisterDeviceRequestObject.DEVICE_PUSH_ID],
                    devicePushIdType=PushIdType.IOS_APNS,
                    deviceDetails=None,
                    createDateTime=None,
                    updateDateTime=None,
                )
            )
            jsonify.assert_called_with({"id": service().register_device()})


if __name__ == "__main__":
    unittest.main()
