import unittest
from unittest.mock import MagicMock, patch

from sdk.common.adapter.alibaba.ali_cloud_sms_adapter import AliCloudSmsAdapter
from sdk.common.adapter.alibaba.exception import SendAlibabaSmsException

ALI_CLOUD_SMS_ADAPTER_PATH = "sdk.common.adapter.alibaba.ali_cloud_sms_adapter"
SAMPLE_PHONE_NUMBER = "+1234567890"
SAMPLE_TEXT = "Simple text."


class AliCloudSMSAdapterTestCase(unittest.TestCase):
    @patch(f"{ALI_CLOUD_SMS_ADAPTER_PATH}.json")
    @patch(f"{ALI_CLOUD_SMS_ADAPTER_PATH}.CommonRequest")
    def test_send_sms(self, mock_common_request, mock_json):
        ali_sms_adapter = AliCloudSmsAdapter(config=MagicMock())
        ali_sms_adapter._client = MagicMock()

        mock_json.loads.return_value = {"ResponseCode": "OK"}

        phone_number: str = SAMPLE_PHONE_NUMBER
        text: str = SAMPLE_TEXT
        phone_number_source: str = ""

        result = ali_sms_adapter.send_sms(
            phone_number=phone_number,
            text=text,
            phone_number_source=phone_number_source,
        )

        mock_common_request().set_accept_format.assert_called_with("json")
        mock_common_request().set_domain.assert_called()
        mock_common_request().set_method.assert_called_with("POST")
        mock_common_request().set_version.assert_called_with("2018-05-01")
        mock_common_request().set_action_name.assert_called_with(
            "SendMessageWithTemplate"
        )
        self.assertEqual(mock_common_request().add_query_param.call_count, 5)

        ali_sms_adapter._client.do_action_with_exception.assert_called_with(
            mock_common_request()
        )

        self.assertEqual(result, "")

    @patch(f"{ALI_CLOUD_SMS_ADAPTER_PATH}.json")
    @patch(f"{ALI_CLOUD_SMS_ADAPTER_PATH}.CommonRequest", MagicMock())
    def test_send_sms_exception(self, mock_json):
        ali_sms_adapter = AliCloudSmsAdapter(config=MagicMock())
        ali_sms_adapter._client = MagicMock()

        mock_json.loads.return_value = {"ResponseCode": "NOT OK"}

        phone_number: str = SAMPLE_PHONE_NUMBER
        text: str = SAMPLE_TEXT
        phone_number_source: str = ""

        with self.assertRaises(SendAlibabaSmsException):
            ali_sms_adapter.send_sms(
                phone_number=phone_number,
                text=text,
                phone_number_source=phone_number_source,
            )


if __name__ == "__main__":
    unittest.main()
