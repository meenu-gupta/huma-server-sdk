from unittest.mock import MagicMock

from extensions.key_action.component import KeyActionComponent
from extensions.tests.test_case import ExtensionTestCase
from extensions.tests.utils import sample_user
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.sms_adapter import SmsAdapter
from sdk.common.adapter.twilio.twilio_sms_verification_adapter import (
    TwilioSmsVerificationAdapter,
)
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from .mock_objects import MockEmailAdapter

BLOOD_PRESSURE_VALID_TITLE = "Test Blood Pressure"
BLOOD_PRESSURE_REMINDER_VALID_DESCRIPTION = "Test BP body"
BLOOD_PRESSURE_KEY_ACTION_VALID_TITLE = "Blood Pressure"
BLOOD_PRESSURE_KEY_ACTION_VALID_DESC = "Time to measure your blood pressure"
APPOINTMENT_DEFAULT_TITLE = "Test appointment"
APPOINTMENT_DEFAULT_BODY = "Test appointment body"
APPOINTMENT_GERMAN_TITLE = "Appointment German"
APPOINTMENT_GERMAN_BODY = "Appointment German body"
VERIFICATION_TEMPLATE = "Test verification template \u200A"


class LocalizationTestCase(ExtensionTestCase):
    components = [AuthComponent(), CalendarComponent(), KeyActionComponent()]
    mocked_sms_adapter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.mocked_sms_adapter = MagicMock()
        mocked_config = MagicMock()
        mocked_config.templateKey = "SMSVerificationTemplate"
        mocked_config.useTwilioVerify = False
        sms_adapter = TwilioSmsVerificationAdapter(
            otp_repo=MagicMock(),
            sms_adapter=cls.mocked_sms_adapter,
            config=mocked_config,
        )

        def mock_adapters(binder: Binder):
            binder.bind(SmsAdapter, cls.mocked_sms_adapter)
            binder.bind(EmailVerificationAdapter, MockEmailAdapter())
            binder.bind("aliCloudSmsVerificationAdapter", sms_adapter)
            binder.bind("twilioSmsVerificationAdapter", sms_adapter)

        inject.get_injector().rebind(mock_adapters)

    def test_send_verification_localization(self):
        body = {
            "method": 1,
            "phoneNumber": sample_user()["phoneNumber"],
            "language": Language.EN,
            "clientId": "ctest1",
            "projectId": "ptest1",
        }

        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=body,
        )
        self.assertEqual(rsp.status_code, 200)
        self.mocked_sms_adapter.send_sms.assert_called_once()
        template = self.mocked_sms_adapter.send_sms.call_args.args[1]
        self.assertEqual(template, VERIFICATION_TEMPLATE)
        self.mocked_sms_adapter.reset_mock()

        # test backward compatibility
        body["language"] = Language.EN
        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=body,
        )
        self.assertEqual(rsp.status_code, 200)
        self.mocked_sms_adapter.send_sms.assert_called_once()
        template = self.mocked_sms_adapter.send_sms.call_args.args[1]
        self.assertEqual(template, VERIFICATION_TEMPLATE)
        self.mocked_sms_adapter.reset_mock()

        # test not supported language switched to default
        body["language"] = "random_language"
        rsp = self.flask_client.post(
            "/api/auth/v1beta/sendverificationtoken",
            json=body,
        )
        self.assertEqual(rsp.status_code, 200)
        self.mocked_sms_adapter.send_sms.assert_called_once()
        template = self.mocked_sms_adapter.send_sms.call_args.args[1]
        self.assertEqual(template, VERIFICATION_TEMPLATE)
