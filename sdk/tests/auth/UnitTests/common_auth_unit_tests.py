from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import Flask, g

from sdk.auth.enums import AuthStage, Method
from sdk.auth.model.auth_user import AuthUser, AuthIdentifier, AuthIdentifierType
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import (
    RefreshTokenRequestObject,
    SignInRequestObject,
    ConfirmationRequestObject,
    BaseAuthRequestObject,
    inject_language,
)
from sdk.auth.use_case.auth_use_cases import (
    RefreshTokenUseCase,
    ConfirmationUseCase,
    mask_phone_number,
)
from sdk.auth.use_case.factories import sign_in_use_case_factory
from sdk.auth.use_case.utils import check_tfa_requirements_met
from sdk.common.adapter.email_adapter import EmailAdapter
from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    EmailNotSetException,
    EmailNotVerifiedException,
    PhoneNumberNotSetException,
    PhoneNumberNotVerifiedException,
    PasswordNotSetException,
    PhoneNumberAlreadyVerifiedException,
    EmailAlreadyVerifiedException,
)
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import (
    USER_CLAIMS_KEY,
    IDENTITY_CLAIM_KEY,
    AUTH_STAGE,
)
from sdk.phoenix.config.server_config import Project, Client, PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH
from sdk.tests.auth.test_helpers import (
    USER_EMAIL,
    USER_PHONE_NUMBER,
    USER_HASHED_PASSWORD_VALUE,
    USER_ID,
    TEST_USER_AGENT,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    USER_PASSWORD,
    CONFIRMATION_CODE,
    get_auth_repo_with_user,
    PROJECT_ID,
)
from sdk.tests.constants import CLIENT_ID

SMS_FACTORY_PATH = "sdk.auth.use_case.utils.SMSAdapterFactory"

test_app = Flask(__name__)


class BaseCommonAuthTestCase(TestCase):
    def setUp(self):
        self.context = test_app.app_context()
        self.context.push()


class TFARequirementsMetMethodUnitTestCase(BaseCommonAuthTestCase):
    def setUp(self) -> None:
        self.verified_identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER, verified=True
        )

    def test_check_tfa_requirements_met__valid(self):
        user = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[self.verified_identifier],
        )
        check_tfa_requirements_met(user)

    def test_check_tfa_requirements_met__raises_email_not_set_exception(self):
        user = AuthUser(
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[self.verified_identifier],
        )
        self.assertRaises(EmailNotSetException, check_tfa_requirements_met, user)

    def test_check_tfa_requirements_met__raises_email_not_verified_exception(self):
        user = AuthUser(
            email=USER_EMAIL,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[self.verified_identifier],
        )
        self.assertRaises(EmailNotVerifiedException, check_tfa_requirements_met, user)

    def test_check_tfa_requirements_met__raises_phone_number_not_set_exception(self):
        user = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
        )
        self.assertRaises(PhoneNumberNotSetException, check_tfa_requirements_met, user)

    def test_check_tfa_requirements_met__raises_phone_number_not_verified_exception(
        self,
    ):
        identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER
        )
        user = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[identifier],
        )
        self.assertRaises(
            PhoneNumberNotVerifiedException, check_tfa_requirements_met, user
        )

    def test_check_tfa_requirements_met__raises_password_not_set_exception(self):
        user = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            mfaIdentifiers=[self.verified_identifier],
        )
        self.assertRaises(PasswordNotSetException, check_tfa_requirements_met, user)


class SessionUnitTestCase(BaseCommonAuthTestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        verified_identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER, verified=True
        )
        self.auth_repo.get_user.return_value = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            status=AuthUser.Status.NORMAL,
            id=USER_ID,
            mfaIdentifiers=[verified_identifier],
        )
        self.token_adapter = MagicMock()
        self.token_adapter.verify_token.return_value = {
            USER_CLAIMS_KEY: {
                "projectId": PROJECT_ID,
                "clientId": CLIENT_ID,
                "method": 0,
                AUTH_STAGE: AuthStage.NORMAL,
            },
            IDENTITY_CLAIM_KEY: USER_ID,
        }
        self.token_adapter.create_access_token.return_value = ACCESS_TOKEN
        self.token_adapter.create_refresh_token.return_value = REFRESH_TOKEN
        self.config = MagicMock()
        self.config.server.project = Project(
            id=PROJECT_ID, clients=[Client(clientId=CLIENT_ID)]
        )
        self.config.server.adapters.aliCloudSms = None

        def bind(binder):
            binder.bind(PhoenixServerConfig, self.config)
            binder.bind(AuthRepository, self.auth_repo)
            binder.bind(TokenAdapter, self.token_adapter)
            binder.bind(OneTimePasswordRepository, MagicMock())
            binder.bind(EmailAdapter, MagicMock())

        inject.clear_and_configure(bind)

    def test_session_updated_on_refresh_token_use_case(self):
        use_case = RefreshTokenUseCase(self.auth_repo, self.config, self.token_adapter)
        request_object = RefreshTokenRequestObject(
            refreshToken=REFRESH_TOKEN, deviceAgent=TEST_USER_AGENT
        )
        use_case.execute(request_object)
        expected_session = DeviceSession(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.update_device_session.assert_called_once_with(expected_session)

    def test_session_created_on_email_sign_in_use_case(self):
        request_object = SignInRequestObject(
            method=Method.EMAIL,
            email=USER_EMAIL,
            deviceAgent=TEST_USER_AGENT,
            projectId=PROJECT_ID,
            clientId=CLIENT_ID,
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        use_case.execute(request_object)
        expected_session = DeviceSessionV1(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.register_device_session.assert_called_once_with(expected_session)

    @patch(SMS_FACTORY_PATH, MagicMock())
    def test_session_created_on_phone_number_sign_in_use_case(self):
        request_object = SignInRequestObject.from_dict(
            {
                SignInRequestObject.METHOD: Method.PHONE_NUMBER,
                SignInRequestObject.PHONE_NUMBER: USER_PHONE_NUMBER,
                SignInRequestObject.DEVICE_AGENT: TEST_USER_AGENT,
                SignInRequestObject.PROJECT_ID: PROJECT_ID,
                SignInRequestObject.CLIENT_ID: CLIENT_ID,
                SignInRequestObject.CONFIRMATION_CODE: "222222",
            }
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        use_case.execute(request_object)
        expected_session = DeviceSessionV1(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.register_device_session.assert_called_once_with(expected_session)

    def test_session_created_on_email_password_sign_in_use_case(self):
        request_object = SignInRequestObject.from_dict(
            {
                SignInRequestObject.METHOD: Method.EMAIL_PASSWORD,
                SignInRequestObject.EMAIL: USER_EMAIL,
                SignInRequestObject.PASSWORD: USER_PASSWORD,
                SignInRequestObject.DEVICE_AGENT: TEST_USER_AGENT,
                SignInRequestObject.PROJECT_ID: PROJECT_ID,
                SignInRequestObject.CLIENT_ID: CLIENT_ID,
            }
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        use_case.execute(request_object)
        expected_session = DeviceSessionV1(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.register_device_session.assert_called_once_with(expected_session)

    def test_session_created_on_tfa_first_factor_sign_in_use_case(self):
        request_object = SignInRequestObject.from_dict(
            {
                SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
                SignInRequestObject.EMAIL: USER_EMAIL,
                SignInRequestObject.PASSWORD: USER_PASSWORD,
                SignInRequestObject.DEVICE_AGENT: TEST_USER_AGENT,
                SignInRequestObject.PROJECT_ID: PROJECT_ID,
                SignInRequestObject.CLIENT_ID: CLIENT_ID,
            }
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        use_case.execute(request_object)
        expected_session = DeviceSessionV1(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.register_device_session.assert_called_once_with(expected_session)

    @patch(SMS_FACTORY_PATH, MagicMock())
    def test_session_updated_on_tfa_second_factor_sign_in_use_case(self):
        self.token_adapter.verify_token.return_value = {
            USER_CLAIMS_KEY: {
                "projectId": PROJECT_ID,
                "clientId": CLIENT_ID,
                "method": 3,
            },
            IDENTITY_CLAIM_KEY: USER_ID,
        }
        request_object = SignInRequestObject.from_dict(
            {
                SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
                SignInRequestObject.DEVICE_AGENT: TEST_USER_AGENT,
                SignInRequestObject.PROJECT_ID: PROJECT_ID,
                SignInRequestObject.CLIENT_ID: CLIENT_ID,
                SignInRequestObject.CONFIRMATION_CODE: CONFIRMATION_CODE,
                SignInRequestObject.REFRESH_TOKEN: REFRESH_TOKEN,
            }
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )

        use_case.execute(request_object)
        expected_session = DeviceSession(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.update_device_session.assert_called_once_with(expected_session)

    @patch(SMS_FACTORY_PATH)
    def test_session_updated_on_tfa_relogin_sign_in_use_case(self, sms_factory):
        sms_factory.get_sms_adapter.return_value = MagicMock()
        self.token_adapter.verify_token.return_value = {
            USER_CLAIMS_KEY: {
                "projectId": PROJECT_ID,
                "clientId": CLIENT_ID,
                "method": 3,
            },
            IDENTITY_CLAIM_KEY: USER_ID,
        }
        request_object = SignInRequestObject(
            method=Method.TWO_FACTOR_AUTH,
            confirmationCode=CONFIRMATION_CODE,
            refreshToken=REFRESH_TOKEN,
            deviceAgent=TEST_USER_AGENT,
            projectId=PROJECT_ID,
            clientId=CLIENT_ID,
        )
        request_object = SignInRequestObject.from_dict(
            {
                SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH,
                SignInRequestObject.DEVICE_AGENT: TEST_USER_AGENT,
                SignInRequestObject.PROJECT_ID: PROJECT_ID,
                SignInRequestObject.CLIENT_ID: CLIENT_ID,
                SignInRequestObject.CONFIRMATION_CODE: CONFIRMATION_CODE,
                SignInRequestObject.REFRESH_TOKEN: REFRESH_TOKEN,
            }
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        use_case.execute(request_object)
        expected_session = DeviceSession(
            userId=USER_ID, deviceAgent=TEST_USER_AGENT, refreshToken=REFRESH_TOKEN
        )
        self.auth_repo.update_device_session.assert_called_once_with(expected_session)


class ConfirmationUnitTestCase(BaseCommonAuthTestCase):
    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), self.phoenix_config
        )

    def test_confirmation_raises_exception_when_trying_to_confirm_phone_number_second_time(
        self,
    ):
        # User have verified phone number and marked as eligible for MFA to trigger sign in use case, but should not
        verified_identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER, verified=True
        )
        user = MagicMock(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            eligible_for_mfa=True,
            mfaIdentifiers=[verified_identifier],
        )
        auth_repo = get_auth_repo_with_user(user)

        data = {
            ConfirmationRequestObject.PHONE_NUMBER: USER_PHONE_NUMBER,
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_data = ConfirmationRequestObject.from_dict(data)
        use_case = ConfirmationUseCase(
            auth_repo,
            MagicMock(),
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
        )
        self.assertRaises(
            PhoneNumberAlreadyVerifiedException, use_case.execute, request_data
        )

    def test_confirmation_raises_exception_when_trying_to_confirm_email_second_time(
        self,
    ):
        # User have verified email and marked as eligible for MFA to trigger sign in use case, but should not
        user = MagicMock(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=True,
            eligible_for_mfa=True,
        )
        auth_repo = get_auth_repo_with_user(user)

        data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_data = ConfirmationRequestObject.from_dict(data)
        use_case = ConfirmationUseCase(
            auth_repo,
            MagicMock(),
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
        )
        self.assertRaises(EmailAlreadyVerifiedException, use_case.execute, request_data)

    def test_confirmation_request_removes_leading_zero(self):
        phone_number_with_zero = "+4407963955051"
        phone_number_without_zero = "+447963955051"
        data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.PHONE_NUMBER: phone_number_with_zero,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
        }
        request_data = ConfirmationRequestObject.from_dict(data)
        self.assertEqual(phone_number_without_zero, request_data.phoneNumber)
        dict_data = request_data.to_dict()
        dict_phone_number = dict_data[ConfirmationRequestObject.PHONE_NUMBER]
        self.assertEqual(phone_number_without_zero, dict_phone_number)


class AttributesTestCase(BaseCommonAuthTestCase):
    def test_masked_phone_number(self):
        sample = "**********095"
        masked_phone_number = mask_phone_number(USER_PHONE_NUMBER)
        self.assertEqual(masked_phone_number, sample)


class InjectLanguageTestCase(BaseCommonAuthTestCase):
    def test_language_injected(self):
        g.language = "en"
        body = {
            BaseAuthRequestObject.CLIENT_ID: "test1",
            BaseAuthRequestObject.PROJECT_ID: "test2",
        }
        inject_language(body)
        self.assertIn(BaseAuthRequestObject.LANGUAGE, body)

    def test_language_not_injected_because_present(self):
        g.language = "incorrectLanguage"
        body = {
            BaseAuthRequestObject.CLIENT_ID: "test1",
            BaseAuthRequestObject.PROJECT_ID: "test2",
            BaseAuthRequestObject.LANGUAGE: "correctLanguage",
        }
        inject_language(body)
        self.assertEqual("correctLanguage", body[BaseAuthRequestObject.LANGUAGE])

    def test_language_not_injected_because_not_in_g(self):
        body = {
            BaseAuthRequestObject.CLIENT_ID: "test1",
            BaseAuthRequestObject.PROJECT_ID: "test2",
        }
        inject_language(body)
        self.assertNotIn(BaseAuthRequestObject.LANGUAGE, body)

    def test_language_not_injected_when_error(self):
        body = {
            BaseAuthRequestObject.CLIENT_ID: "test1",
            BaseAuthRequestObject.PROJECT_ID: "test2",
        }
        self.context.pop()
        try:
            inject_language(body)
        except Exception as e:
            self.fail(str(e))
