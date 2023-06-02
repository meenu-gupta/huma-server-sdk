import unittest
from pathlib import Path
from unittest.mock import MagicMock

from sdk.auth.enums import Method
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import (
    SignInRequestObject,
    SignInRequestObjectV1,
)
from sdk.auth.use_case.factories import (
    sign_in_use_case_factory,
    sign_in_use_case_factory_v1,
)
from sdk.auth.use_case.sign_in_use_cases.email_password_sign_in_use_case import (
    EmailPasswordSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.email_sign_in_use_case import (
    EmailSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.first_factor_sign_in_use_case import (
    TFAFirstFactorSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.phone_number_sign_in_use_case import (
    PhoneNumberSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.remember_me_sign_in_use_case import (
    RememberMeSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.second_factor_sign_in_use_case import (
    TFASecondFactorSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.second_factor_sign_in_use_case_v1 import (
    TFASecondFactorSignInUseCaseV1,
)
from sdk.common.adapter.email_adapter import EmailAdapter
from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config

SAMPLE_EMAIL = "test@gmail.com"
SAMPLE_PASSWORD = "password"
SAMPLE_PHONE_NUMBER = "+441347722095"
SDK_CONFIG_PATH = str(Path(__file__).with_name("config.test.yaml"))


class SignInUseCaseFactoriesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)

        def bind_and_configure(binder):
            binder.bind(PhoenixServerConfig, phoenix_config)
            binder.bind(AuthRepository, MagicMock())
            binder.bind(TokenAdapter, MagicMock())
            binder.bind(OneTimePasswordRepository, MagicMock())
            binder.bind(EmailAdapter, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    @staticmethod
    def _get_request_object(
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ) -> SignInRequestObject:
        data = {
            SignInRequestObject.METHOD: method,
            SignInRequestObject.EMAIL: email,
            SignInRequestObject.PHONE_NUMBER: phone_number,
            SignInRequestObject.PASSWORD: password,
            SignInRequestObject.REFRESH_TOKEN: refresh_token,
            SignInRequestObject.CONFIRMATION_CODE: confirmation_code or "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
            SignInRequestObject.DEVICE_AGENT: "chrome",
        }
        return SignInRequestObject.from_dict(remove_none_values(data))

    def test_email_use_case(self):
        request_object = self._get_request_object(
            method=Method.EMAIL, email=SAMPLE_EMAIL
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, EmailSignInUseCase))

    def test_phone_number_use_case(self):
        request_object = self._get_request_object(
            method=Method.PHONE_NUMBER, phone_number=SAMPLE_PHONE_NUMBER
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, PhoneNumberSignInUseCase))

    def test_email_password_first_factor_use_case(self):
        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH, email=SAMPLE_EMAIL, password=SAMPLE_PASSWORD
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, TFAFirstFactorSignInUseCase))

    def test_email_password_use_case(self):
        request_object = self._get_request_object(
            method=Method.EMAIL_PASSWORD, email=SAMPLE_EMAIL, password=SAMPLE_PASSWORD
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, EmailPasswordSignInUseCase))

    def test_email_password_second_factor_use_case(self):
        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH, email=SAMPLE_EMAIL, refresh_token="token"
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, TFASecondFactorSignInUseCase))

    def test_failure_without_confirmation_code_use_case(self):
        with self.assertRaises(ConvertibleClassValidationError):
            self._get_request_object(
                method=Method.TWO_FACTOR_AUTH, email=SAMPLE_EMAIL, confirmation_code=""
            )


class SignInUseCaseFactoriesV1TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)

        def bind_and_configure(binder):
            binder.bind(PhoenixServerConfig, phoenix_config)
            binder.bind(AuthRepository, MagicMock())
            binder.bind(TokenAdapter, MagicMock())
            binder.bind(OneTimePasswordRepository, MagicMock())
            binder.bind(EmailAdapter, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    @staticmethod
    def _get_request_object(
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ) -> SignInRequestObject:
        data = {
            SignInRequestObject.METHOD: method,
            SignInRequestObject.EMAIL: email,
            SignInRequestObject.PHONE_NUMBER: phone_number,
            SignInRequestObject.PASSWORD: password,
            SignInRequestObject.REFRESH_TOKEN: refresh_token,
            SignInRequestObject.CONFIRMATION_CODE: confirmation_code or "123",
            SignInRequestObject.CLIENT_ID: "ctest1",
            SignInRequestObject.PROJECT_ID: "ptest1",
            SignInRequestObject.DEVICE_AGENT: "chrome",
        }
        return SignInRequestObjectV1.from_dict(remove_none_values(data))

    def test_email_password_second_factor_use_case(self):
        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH, email=SAMPLE_EMAIL, refresh_token="token"
        )
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, TFASecondFactorSignInUseCaseV1))

    def test_remember_me_use_case(self):
        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH,
            email=SAMPLE_EMAIL,
            password=SAMPLE_PASSWORD,
            refresh_token="token",
        )
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        self.assertTrue(isinstance(use_case, RememberMeSignInUseCase))
