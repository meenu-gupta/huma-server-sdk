import unittest
from datetime import datetime
from unittest.mock import MagicMock

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from sdk.auth.use_case.auth_request_objects import SignUpRequestObject
from sdk.auth.use_case.auth_use_cases import SignUpUseCase
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.exceptions.exceptions import InvalidEmailConfirmationCodeException
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH
from sdk.tests.auth.UnitTests.base_auth_request_tests import BaseAuthTestCase
from sdk.tests.auth.mock_objects import sample_sign_up_data
from sdk.tests.auth.test_helpers import USER_EMAIL

INVALID_USER_EMAIL = "invalid_user@test.com"


class EmailPasswordAUthTestCase(unittest.TestCase):
    def test_password_validation_during_sign_up(self):
        data = sample_sign_up_data()

        # Less than 8 symbols
        data[SignUpRequestObject.PASSWORD] = "1234567"
        with self.assertRaises(ConvertibleClassValidationError):
            SignUpRequestObject.from_dict(data)

        # No letters in password
        data[SignUpRequestObject.PASSWORD] = "12345678"
        with self.assertRaises(ConvertibleClassValidationError):
            SignUpRequestObject.from_dict(data)

        # No upper case letter in password
        data[SignUpRequestObject.PASSWORD] = "a2345678"
        with self.assertRaises(ConvertibleClassValidationError):
            SignUpRequestObject.from_dict(data)

        # No digits in password
        data[SignUpRequestObject.PASSWORD] = "abcqwertY"
        with self.assertRaises(ConvertibleClassValidationError):
            SignUpRequestObject.from_dict(data)


class JwtConfirmationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        cfg = PhoenixServerConfig.get(SDK_CONFIG_PATH, {})
        self.token_adapter = JwtTokenAdapter(JwtTokenConfig(secret="test"), cfg)
        self.confirmation_adapter = EmailConfirmationAdapter(
            cfg, self.token_adapter, MagicMock(), MagicMock()
        )

    def test_confirmation_token_valid(self):
        # confirming token valid at creation moment
        token = self.token_adapter.create_confirmation_token(USER_EMAIL)
        code = self.confirmation_adapter.verify_code(
            token, USER_EMAIL, EmailConfirmationAdapter.CONFIRMATION_CODE_TYPE
        )
        self.assertTrue(code)

    def test_token_expires_after_24_hours(self):
        token = self.token_adapter.create_confirmation_token(USER_EMAIL)
        # confirming token invalid after 24h
        with freeze_time(datetime.utcnow() + relativedelta(days=1, minutes=1)):
            with self.assertRaises(InvalidEmailConfirmationCodeException):
                self.confirmation_adapter.verify_code(
                    token, USER_EMAIL, EmailConfirmationAdapter.CONFIRMATION_CODE_TYPE
                )

    def test_token_valid_during_24_hours(self):
        token = self.token_adapter.create_confirmation_token(USER_EMAIL)
        # confirming token valid during 24h
        with freeze_time(datetime.utcnow() + relativedelta(hour=23, minutes=59)):
            self.assertTrue(
                self.confirmation_adapter.verify_code(
                    token, USER_EMAIL, EmailConfirmationAdapter.CONFIRMATION_CODE_TYPE
                )
            )

    def test_token_valid_only_for_users_email(self):
        # confirming token valid at creation moment
        token = self.token_adapter.create_confirmation_token(USER_EMAIL)
        with self.assertRaises(InvalidEmailConfirmationCodeException):
            self.confirmation_adapter.verify_code(
                token,
                INVALID_USER_EMAIL,
                EmailConfirmationAdapter.CONFIRMATION_CODE_TYPE,
            )


class PasswordTestCase(BaseAuthTestCase):
    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)

    def test_password_update_datetime_set_on_signup(self):
        data = sample_sign_up_data()
        request_obj = SignUpRequestObject.from_dict(data)
        mocked_auth_repo = MagicMock()
        use_case = SignUpUseCase(
            mocked_auth_repo, self.phoenix_config, MagicMock(), MagicMock()
        )
        use_case.execute(request_obj)
        mocked_auth_repo.create_user.assert_called_once()
        args = mocked_auth_repo.create_user.call_args
        auth_user = args.kwargs.get("auth_user")
        self.assertIsNotNone(auth_user.passwordUpdateDateTime)
        self.assertEqual(
            auth_user.passwordUpdateDateTime, auth_user.passwordCreateDateTime
        )


if __name__ == "__main__":
    unittest.main()
