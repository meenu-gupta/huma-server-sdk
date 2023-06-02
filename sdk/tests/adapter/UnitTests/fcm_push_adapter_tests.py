import unittest
from unittest.mock import MagicMock, patch

from firebase_admin.exceptions import FirebaseError

from sdk.common.adapter.fcm.fcm_push_adapter import FCMPushAdapter

FCM_PUSH_ADAPTER_PATH = "sdk.common.adapter.fcm.fcm_push_adapter"
ANDROID_MESSAGE = MagicMock(notification=MagicMock(title="Title", body="Message body"))


class FCMPushAdapterTestCase(unittest.TestCase):
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.Certificate", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.firebase_admin.initialize_app", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.messaging")
    def test_send_message_to_identities_one(self, mock_messaging):
        fcm_push_adapter = FCMPushAdapter(config=MagicMock())

        identities = ["one"]
        android_message = ANDROID_MESSAGE

        fcm_push_adapter.send_message_to_identities(
            identities=identities, message=android_message
        )
        mock_messaging.Message.assert_called()
        mock_messaging.send.assert_called()

    @patch(f"{FCM_PUSH_ADAPTER_PATH}.Certificate", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.firebase_admin.initialize_app", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.messaging")
    def test_send_message_to_identities_one_exception(self, mock_messaging):
        fcm_push_adapter = FCMPushAdapter(config=MagicMock())
        http_response = MagicMock()
        http_response.status_code = 400
        mock_messaging.send.side_effect = FirebaseError(message="error", code=400, http_response=http_response)

        identities = ["one"]
        android_message = ANDROID_MESSAGE

        output = fcm_push_adapter.send_message_to_identities(
            identities=identities, message=android_message
        )
        self.assertEqual(output, identities)

        http_response.status_code = 401
        mock_messaging.send.side_effect = FirebaseError(message="error", code=401, http_response=http_response)

        with self.assertRaises(FirebaseError):
            fcm_push_adapter.send_message_to_identities(
                identities=identities, message=android_message
            )

    @patch(f"{FCM_PUSH_ADAPTER_PATH}.Certificate", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.firebase_admin.initialize_app", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.messaging.send_all")
    def test_send_message_to_identities_multiple(self, mock_send_all):
        fcm_push_adapter = FCMPushAdapter(config=MagicMock())

        identities = ["one", "two"]
        android_message = ANDROID_MESSAGE

        fcm_push_adapter.send_message_to_identities(
            identities=identities, message=android_message
        )

        mock_send_all.assert_called_once()

    @patch(f"{FCM_PUSH_ADAPTER_PATH}.Certificate", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.firebase_admin.initialize_app", MagicMock())
    @patch(f"{FCM_PUSH_ADAPTER_PATH}.messaging")
    def test_send_message_to_identities_multiple_exception(self, mock_messaging):
        fcm_push_adapter = FCMPushAdapter(config=MagicMock())
        response = MagicMock()
        response.exception.http_response.status_code = 400

        responses = [response, response]
        batch_rsp = MagicMock()
        batch_rsp.responses = responses
        mock_messaging.send_all.return_value = batch_rsp

        identities = ["one", "two"]
        android_message = ANDROID_MESSAGE

        output = fcm_push_adapter.send_message_to_identities(
            identities=identities, message=android_message
        )
        self.assertEqual(output, identities)

        mock_messaging.send_all.side_effect = FirebaseError(message="error", code="code")

        with self.assertRaises(FirebaseError):
            fcm_push_adapter.send_message_to_identities(
                identities=identities, message=android_message
            )


if __name__ == "__main__":
    unittest.main()
