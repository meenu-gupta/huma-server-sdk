import unittest
from unittest.mock import MagicMock, patch

from sdk.common.adapter.sms_adapter_factory import SMSAdapterFactory


class ConfigAdaptersMock:
    aliCloudSms = MagicMock()


class SMSAdapterFactoryTestCase(unittest.TestCase):
    @patch("sdk.common.adapter.sms_adapter_factory.inject")
    def test_success_inject_alicloud_sms_adapter(self, inject):
        SMSAdapterFactory.get_sms_adapter(ConfigAdaptersMock, "+865555")
        inject.instance.assert_called_with("aliCloudSmsVerificationAdapter")

    @patch("sdk.common.adapter.sms_adapter_factory.inject")
    def test_success_inject_twillio_sms_adapter__no_alicloud_adapter_chinese_phone_number(
        self, inject
    ):
        ConfigAdaptersMock.aliCloudSms = None
        SMSAdapterFactory.get_sms_adapter(ConfigAdaptersMock, "+865555")
        inject.instance.assert_called_with("twilioSmsVerificationAdapter")

    @patch("sdk.common.adapter.sms_adapter_factory.inject")
    def test_success_inject_twillio_sms_adapter__not_chinese_phone_number(self, inject):
        SMSAdapterFactory.get_sms_adapter(ConfigAdaptersMock, "+380555")
        inject.instance.assert_called_with("twilioSmsVerificationAdapter")


if __name__ == "__main__":
    unittest.main()
