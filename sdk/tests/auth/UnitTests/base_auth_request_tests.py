import unittest
from pathlib import Path
from unittest.mock import MagicMock

from sdk.auth.use_case.auth_request_objects import BaseAuthRequestObject
from sdk.common.adapter.email_adapter import EmailAdapter
from sdk.common.exceptions.exceptions import (
    InvalidClientIdException,
    InvalidProjectIdException,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.tests.auth.mock_objects import MockSmsAdapter


class BaseAuthTestCase(unittest.TestCase):
    sms_adapter = MockSmsAdapter()

    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            config_path = Path(__file__).parent.joinpath("config.test.yaml")
            config = PhoenixServerConfig.get(config_path, {})
            binder.bind(PhoenixServerConfig, config)
            binder.bind(EmailAdapter, MagicMock())
            binder.bind("aliCloudSmsVerificationAdapter", cls.sms_adapter)
            binder.bind("twilioSmsVerificationAdapter", cls.sms_adapter)

        inject.clear_and_configure(bind)

    def tearDown(self) -> None:
        self.sms_adapter.send_verification_code.reset_mock()


class AuthRequestObjectTestCase(BaseAuthTestCase):
    def test_success_request_object(self):
        try:
            BaseAuthRequestObject.from_dict(
                {
                    BaseAuthRequestObject.LANGUAGE: "en",
                    BaseAuthRequestObject.CLIENT_ID: "ctest1",
                    BaseAuthRequestObject.PROJECT_ID: "ptest1",
                }
            )
        except (InvalidClientIdException, InvalidProjectIdException):
            self.fail()

    def test_failure_with_invalid_client_id(self):
        with self.assertRaises(InvalidClientIdException):
            BaseAuthRequestObject.from_dict(
                {
                    BaseAuthRequestObject.LANGUAGE: "en",
                    BaseAuthRequestObject.CLIENT_ID: "invalid client id",
                    BaseAuthRequestObject.PROJECT_ID: "ptest1",
                }
            )

    def test_failure_with_invalid_project_id(self):
        with self.assertRaises(InvalidProjectIdException):
            BaseAuthRequestObject.from_dict(
                {
                    BaseAuthRequestObject.LANGUAGE: "en",
                    BaseAuthRequestObject.CLIENT_ID: "ctest1",
                    BaseAuthRequestObject.PROJECT_ID: "invalid project id",
                }
            )
