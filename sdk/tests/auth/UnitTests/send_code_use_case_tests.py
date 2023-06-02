from unittest.mock import patch, MagicMock

from twilio.base.exceptions import TwilioRestException

from sdk.auth.use_case.auth_request_objects import SendVerificationTokenRequestObject
from sdk.auth.use_case.auth_use_cases import SendVerificationTokenUseCase
from sdk.common.adapter.twilio.twilio_sms_adapter import (
    TWILIO_INVALID_PHONE_NUMBER_CODE,
    TWILIO_INVALID_FROM_PHONE_NUMBER,
    TwilioSmsAdapter,
)
from sdk.common.adapter.twilio.twilio_sms_config import TwilioSmsConfig
from sdk.common.adapter.twilio.twilio_sms_verification_adapter import (
    TwilioSmsVerificationAdapter,
)
from sdk.common.exceptions.exceptions import (
    InvalidPhoneNumberException,
    InvalidRequestException,
)
from sdk.phoenix.config.server_config import Project, Client
from sdk.tests.auth.UnitTests.base_auth_request_tests import BaseAuthTestCase
from sdk.tests.auth.test_helpers import PROJECT_ID, TEST_CLIENT_ID

SMS_FACTORY_PATH = "sdk.auth.use_case.auth_use_cases.SMSAdapterFactory"


class SendCodeUseCaseTest(BaseAuthTestCase):
    @staticmethod
    def _prepare_use_case():
        phoenix_config = MagicMock()
        phoenix_config.server.adapters.aliCloudSms = False
        project = Project(id=PROJECT_ID, clients=[Client(clientId=TEST_CLIENT_ID)])
        phoenix_config.server.project = project
        return SendVerificationTokenUseCase(
            repo=MagicMock(),
            token_adapter=MagicMock(),
            config=phoenix_config,
            email_verify_adapter=MagicMock(),
            email_confirmation_adapter=MagicMock(),
        )

    @patch("sdk.common.adapter.twilio.twilio_sms_adapter.Client")
    @patch(SMS_FACTORY_PATH)
    def test_send_twilio_sms_raises_proper_exception(
        self, sms_factory, mocked_twilio_client
    ):
        sms_config = TwilioSmsConfig()
        sms_adapter = TwilioSmsAdapter(sms_config)
        sms_verification_config = MagicMock()
        sms_verification_config.useTwilioVerify = False
        sms_factory.get_sms_adapter.return_value = TwilioSmsVerificationAdapter(
            MagicMock(), sms_adapter, sms_verification_config, MagicMock()
        )
        invalid_phone = TwilioRestException(
            status=400, uri="some", code=TWILIO_INVALID_PHONE_NUMBER_CODE
        )
        invalid_from = TwilioRestException(
            status=400, uri="some", code=TWILIO_INVALID_FROM_PHONE_NUMBER
        )
        other_exception = Exception("some issue")
        mocked_twilio_client().messages.create.side_effect = [
            invalid_phone,
            invalid_from,
            other_exception,
        ]

        data = {
            SendVerificationTokenRequestObject.CLIENT_ID: TEST_CLIENT_ID,
            SendVerificationTokenRequestObject.PROJECT_ID: PROJECT_ID,
            SendVerificationTokenRequestObject.METHOD: 1,
            SendVerificationTokenRequestObject.PHONE_NUMBER: "+380500000000",
        }
        request_object = SendVerificationTokenRequestObject.from_dict(data)
        use_case = self._prepare_use_case()
        # raising invalid phone number exception
        with self.assertRaises(InvalidPhoneNumberException):
            use_case.execute(request_object)
        # raising proper exception for twilio exception
        with self.assertRaises(InvalidRequestException):
            use_case.execute(request_object)
        # raising proper exception for any other exception
        with self.assertRaises(InvalidRequestException):
            use_case.execute(request_object)
