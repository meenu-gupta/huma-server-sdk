from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from sdk.auth.enums import AuthStage, Method
from sdk.auth.model.auth_user import AuthUser, AuthIdentifier, AuthIdentifierType
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import (
    SignInRequestObject,
    ConfirmationRequestObject,
    SignInRequestObjectV1,
)
from sdk.auth.use_case.auth_use_cases import (
    ConfirmationUseCase,
    TFAOldUserConfirmationSignInUseCase,
    EmailConfirmationSignInUseCase,
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
from sdk.auth.use_case.utils import (
    TEST_PHONE_NUMBER,
    TEST_CONFIRMATION_CODE,
    PACIFIER_CONFIRMATION_CODE,
    PACIFIER_EMAIL,
)
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    PasswordExpiredException,
    InvalidTokenProviderException,
    InvalidVerificationCodeException,
    EmailNotVerifiedException,
    PasswordNotSetException,
    WrongTokenException,
)
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import (
    USER_CLAIMS_KEY,
    IDENTITY_CLAIM_KEY,
    AUTH_STAGE,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client, Project
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH
from sdk.tests.auth.test_helpers import (
    filled_auth_user,
    get_auth_repo_with_user,
    USER_PHONE_NUMBER,
    USER_ID,
    USER_PASSWORD,
    USER_EMAIL,
    USER_HASHED_PASSWORD_VALUE,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    TEST_USER_AGENT,
    PROJECT_ID,
)
from sdk.tests.constants import CLIENT_ID
from .base_auth_request_tests import BaseAuthTestCase

POST_SIGN_IN_MOCK_PATH = "sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case.BaseSignInMethodUseCase._post_sign_in_auth"


def prepare_first_factor_refresh_token(
    token_adapter, identity, method: Method = Method.TWO_FACTOR_AUTH
):
    claims = {
        "projectId": "ptest1",
        "clientId": "ctest1",
        "method": method,
        "secondFactorRequired": True,
        "authStage": AuthStage.FIRST.value,
    }
    return token_adapter.create_refresh_token(identity=identity, user_claims=claims)


class BaseSignInTestCase(BaseAuthTestCase):
    sample_client = None
    phoenix_config = None
    token_adapter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        cls.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), cls.phoenix_config
        )
        cls.sample_client = cls.phoenix_config.server.project.clients[0]

    def setUp(self) -> None:
        self.sample_identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER
        )
        self.sample_identifier_verified = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER, value=USER_PHONE_NUMBER, verified=True
        )

    @staticmethod
    def _get_request_object(
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ) -> SignInRequestObject:
        # signin with email
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

    @staticmethod
    def _get_request_object_v1(
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ) -> SignInRequestObject:
        # signin with email
        data = {
            SignInRequestObjectV1.METHOD: method,
            SignInRequestObjectV1.EMAIL: email,
            SignInRequestObjectV1.PHONE_NUMBER: phone_number,
            SignInRequestObjectV1.PASSWORD: password,
            SignInRequestObjectV1.REFRESH_TOKEN: refresh_token,
            SignInRequestObjectV1.CONFIRMATION_CODE: confirmation_code or "123",
            SignInRequestObjectV1.CLIENT_ID: "ctest1",
            SignInRequestObjectV1.PROJECT_ID: "ptest1",
            SignInRequestObjectV1.DEVICE_AGENT: "chrome",
        }
        return SignInRequestObjectV1.from_dict(remove_none_values(data))

    def _bind(self, auth_repo, token_adapter=None, phoenix_config=None):
        if not phoenix_config:
            phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)

        if not token_adapter:
            token_adapter = JwtTokenAdapter(
                JwtTokenConfig(secret="test"), phoenix_config
            )

        def bind_and_configure(binder):
            binder.bind(AuthRepository, auth_repo)
            binder.bind(PhoenixServerConfig, phoenix_config)
            binder.bind(TokenAdapter, token_adapter)
            binder.bind(EmailVerificationAdapter, MagicMock())
            binder.bind(EventBusAdapter, MagicMock())
            binder.bind("aliCloudSmsVerificationAdapter", self.sms_adapter)
            binder.bind("twilioSmsVerificationAdapter", self.sms_adapter)

        inject.clear_and_configure(bind_and_configure)


class SignInTestCase(BaseSignInTestCase):
    def execute_sign_in_use_case(
        self,
        auth_repo,
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ):
        request_object = self._get_request_object(
            method=method,
            email=email,
            phone_number=phone_number,
            password=password,
            refresh_token=refresh_token,
            confirmation_code=confirmation_code,
        )

        self._bind(auth_repo)
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        result = use_case.execute(request_object).value.to_dict()
        return result, request_object

    def execute_sign_in_use_case_v1(
        self,
        auth_repo,
        method,
        email=None,
        phone_number=None,
        password=None,
        refresh_token=None,
        confirmation_code=None,
    ):
        request_object = self._get_request_object_v1(
            method=method,
            email=email,
            phone_number=phone_number,
            password=password,
            refresh_token=refresh_token,
            confirmation_code=confirmation_code,
        )

        self._bind(auth_repo)
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        result = use_case.execute(request_object).value.to_dict()
        return result, request_object

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__forbidden_with_email_token(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # sign in with email
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo, method=Method.EMAIL, email=USER_EMAIL
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)
        email_refresh_token = result["refreshToken"]

        # confirming that can't auth with email token
        with self.assertRaises(InvalidTokenProviderException):
            self.execute_sign_in_use_case(
                auth_repo=auth_repo,
                method=Method.TWO_FACTOR_AUTH,
                refresh_token=email_refresh_token,
            )
        post_sign_in_mock.assert_not_called()

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__forbidden_with_phone_token(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with phone number
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.PHONE_NUMBER,
            phone_number=user.phoneNumber,
        )

        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)
        phone_refresh_token = result["refreshToken"]

        # confirming that can't auth with phone number token
        with self.assertRaises(InvalidTokenProviderException):
            self.execute_sign_in_use_case(
                auth_repo=auth_repo,
                method=Method.TWO_FACTOR_AUTH,
                refresh_token=phone_refresh_token,
            )
        post_sign_in_mock.assert_not_called()

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__fail_with_email_password_token(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with email + password
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.EMAIL_PASSWORD,
            email=USER_EMAIL,
            password=USER_PASSWORD,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)
        email_password_refresh_token = result["refreshToken"]

        # fail to auth with email-password token
        with self.assertRaises(InvalidTokenProviderException):
            self.execute_sign_in_use_case(
                auth_repo=auth_repo,
                method=Method.TWO_FACTOR_AUTH,
                refresh_token=email_password_refresh_token,
            )

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__valid_with_email_password_first_factor(
        self, post_sign_in_mock
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with email + password
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.TWO_FACTOR_AUTH,
            email=USER_EMAIL,
            password=USER_PASSWORD,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        self.assertEqual(result["uid"], USER_ID)
        first_factor_refresh_token = result.get("refreshToken")
        self.assertIsNotNone(first_factor_refresh_token)
        decoded_token = self.token_adapter.verify_token(
            first_factor_refresh_token, "refresh"
        )
        self.assertEqual(decoded_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.FIRST)

    def test_failure_tfa_sign_in__valid_with_email_password_first_factor(self):
        user = filled_auth_user()
        user.emailVerified = False
        auth_repo = get_auth_repo_with_user(user)

        self._bind(auth_repo)
        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH, email=USER_EMAIL, password=USER_PASSWORD
        )
        with self.assertRaises(EmailNotVerifiedException):
            TFAFirstFactorSignInUseCase().execute(request_object)

        user.emailVerified = True
        user.hashedPassword = ""
        with self.assertRaises(PasswordNotSetException):
            TFAFirstFactorSignInUseCase().execute(request_object)

    def test_mfa_sign_in__fail_with_not_confirmed_email(self):
        user = filled_auth_user()
        user.emailVerified = False
        auth_repo = get_auth_repo_with_user(user)
        self._bind(auth_repo)
        # sign in with email + password
        with self.assertRaises(EmailNotVerifiedException):
            self.execute_sign_in_use_case(
                auth_repo=auth_repo,
                method=Method.TWO_FACTOR_AUTH,
                email=USER_EMAIL,
                password=USER_PASSWORD,
            )

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__second_factor_valid_with_first_factor_token_and_code(
        self, post_sign_in_mock
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        first_factor_token = prepare_first_factor_refresh_token(
            self.token_adapter, user.id
        )

        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.TWO_FACTOR_AUTH,
            refresh_token=first_factor_token,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        mfa_refresh_token = result.get("refreshToken")
        self.assertIsNotNone(mfa_refresh_token)
        decoded_mfa_refresh_token = self.token_adapter.verify_token(
            mfa_refresh_token, "refresh"
        )
        self.assertIsNone(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY].get("secondFactorRequired")
        )
        self.assertEqual(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY]["method"], Method.TWO_FACTOR_AUTH
        )

        auth_token = result.get("authToken")
        self.assertIsNotNone(auth_token)
        decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
        self.assertEqual(
            decoded_auth_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND
        )

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_tfa_sign_in__second_factor_valid_with_first_factor_token_and_code_v1(
        self, post_sign_in_mock
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        first_factor_token = prepare_first_factor_refresh_token(
            self.token_adapter, user.id
        )

        result, request_data = self.execute_sign_in_use_case_v1(
            auth_repo=auth_repo,
            method=Method.TWO_FACTOR_AUTH,
            refresh_token=first_factor_token,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        mfa_refresh_token = result.get("refreshToken")
        self.assertIsNotNone(mfa_refresh_token)
        decoded_mfa_refresh_token = self.token_adapter.verify_token(
            mfa_refresh_token, "refresh"
        )
        self.assertIsNone(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY].get("secondFactorRequired")
        )
        self.assertEqual(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY]["method"], Method.TWO_FACTOR_AUTH
        )

        auth_token = result.get("authToken")
        self.assertIsNotNone(auth_token)
        decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
        self.assertEqual(
            decoded_auth_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND
        )

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__with_email(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with email
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.EMAIL,
            email=USER_EMAIL,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)

    def test_failure_email_sign_in_use_case(self):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=PACIFIER_EMAIL,
            emailVerified=True,
            hashedPassword="",
        )
        auth_repo = get_auth_repo_with_user(user)

        self._bind(auth_repo)
        request_object = self._get_request_object(
            method=Method.EMAIL,
            email=PACIFIER_EMAIL,
            confirmation_code=PACIFIER_CONFIRMATION_CODE,
        )
        EmailSignInUseCase().execute(request_object)
        auth_repo.confirm_email.assert_not_called()

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__with_phone_number(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with phone number
        self._bind(auth_repo)
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.PHONE_NUMBER,
            phone_number=USER_PHONE_NUMBER,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__with_email_password(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with email + password
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.EMAIL_PASSWORD,
            email=USER_EMAIL,
            password=USER_PASSWORD,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)

    def test_failure_sign_in_with_email_password(self):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword="",
        )
        auth_repo = get_auth_repo_with_user(user)
        self._bind(auth_repo)

        request_object = self._get_request_object(
            method=Method.EMAIL_PASSWORD,
            email=USER_EMAIL,
            password=USER_PASSWORD,
        )

        use_case = EmailPasswordSignInUseCase()

        with self.assertRaises(PasswordNotSetException):
            use_case.execute(request_object)

        user.emailVerified = False
        auth_repo = get_auth_repo_with_user(user)
        self._bind(auth_repo)

        with self.assertRaises(EmailNotVerifiedException):
            use_case.execute(request_object)

    def test_fail_sign_in_on_expired_password(self):
        config = MagicMock()
        config.server.project = Project(
            id=PROJECT_ID, clients=[Client(clientId=CLIENT_ID)]
        )
        config.server.adapters.aliCloudSms = None

        # testing password expires in 30 days
        expires_in_days = 30
        clients = [
            Client(clientId=CLIENT_ID, passwordExpiresIn=expires_in_days),
            Client(clientId="otherClient"),
        ]
        project = Project(id=PROJECT_ID, clients=clients)
        config.server.project = project
        expired_password_date_time = datetime.utcnow() - timedelta(
            days=expires_in_days + 1
        )

        auth_repo = MagicMock()
        auth_repo.get_user.return_value = AuthUser(
            email=USER_EMAIL,
            emailVerified=True,
            phoneNumber=USER_PHONE_NUMBER,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            passwordUpdateDateTime=expired_password_date_time,
            status=AuthUser.Status.NORMAL,
            id=USER_ID,
        )
        token_adapter = MagicMock()
        token_adapter.verify_token.return_value = {
            USER_CLAIMS_KEY: {
                "projectId": PROJECT_ID,
                "clientId": CLIENT_ID,
                "method": 0,
            },
            IDENTITY_CLAIM_KEY: USER_ID,
        }
        token_adapter.create_access_token.return_value = ACCESS_TOKEN
        token_adapter.create_refresh_token.return_value = REFRESH_TOKEN

        self._bind(auth_repo, token_adapter, config)
        request_object = SignInRequestObject(
            method=Method.PHONE_NUMBER,
            phoneNumber=USER_PHONE_NUMBER,
            deviceAgent=TEST_USER_AGENT,
            projectId=PROJECT_ID,
            clientId=CLIENT_ID,
        )
        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )
        with self.assertRaises(PasswordExpiredException):
            use_case.execute(request_object)

        # confirming it not expires in 30 days for another client without expiration date specified
        request_object = SignInRequestObject(
            method=Method.PHONE_NUMBER,
            phoneNumber=USER_PHONE_NUMBER,
            deviceAgent=TEST_USER_AGENT,
            projectId=PROJECT_ID,
            clientId="otherClient",
        )
        use_case.execute(request_object)

        # confirming it expires in 60 days (by default) for another client
        with freeze_time(datetime.utcnow() + timedelta(days=30)):
            with self.assertRaises(PasswordExpiredException):
                use_case.execute(request_object)

    @patch("sdk.auth.use_case.auth_use_cases.TFAOldUserConfirmationSignInUseCase")
    def test_sign_in_happens_on_confirmation_when_eligible_for_mfa(
        self, sign_in_use_case_mock
    ):
        # User does not have verified phone number to allow verify it,
        # and marked as eligible for MFA to trigger sign in use case
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            phoneNumber=USER_PHONE_NUMBER,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            email=USER_EMAIL,
            emailVerified=True,
            mfaIdentifiers=[self.sample_identifier],
        )
        user_verified = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            phoneNumber=USER_PHONE_NUMBER,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            email=USER_EMAIL,
            emailVerified=True,
            mfaIdentifiers=[self.sample_identifier_verified],
        )

        auth_repo = get_auth_repo_with_user(user)
        auth_repo.get_user.side_effect = [user, user_verified]

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
        use_case.execute(request_data).value.to_dict()
        sign_in_use_case_mock().execute.assert_called_once_with(request_data)

    @patch("sdk.auth.use_case.auth_use_cases.TFAOldUserConfirmationSignInUseCase")
    def test_sign_in_not_happens_on_confirmation_when_not_eligible_for_mfa(
        self, sign_in_use_case_mock
    ):
        # User does not have verified phone number to allow verify it,
        # and marked as NOT eligible for MFA to check that sign in use case not triggered
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            phoneNumber=USER_PHONE_NUMBER,
            email=USER_EMAIL,
            mfaIdentifiers=[self.sample_identifier],
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
        use_case.execute(request_data).value.to_dict()
        sign_in_use_case_mock().execute.assert_not_called()

    def test_sign_in_old_user_on_confirmation_use_case__with_email_confirmation(self):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[self.sample_identifier_verified],
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
        request_object = ConfirmationRequestObject.from_dict(data)
        use_case = TFAOldUserConfirmationSignInUseCase(
            auth_repo,
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
            MagicMock(),
        )
        result = use_case.execute(request_object).value.to_dict()
        refresh_token = result.get("refreshToken")
        auth_token = result.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # Confirming tokens are valid for MFA
        decoded_ref_token = self.token_adapter.verify_token(refresh_token, "refresh")
        self.assertEqual(
            Method.TWO_FACTOR_AUTH, decoded_ref_token[USER_CLAIMS_KEY]["method"]
        )
        decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
        self.assertEqual(
            decoded_auth_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND
        )

    def test_sign_in_old_user_on_confirmation_use_case__with_phone_number_confirmation(
        self,
    ):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
            mfaIdentifiers=[self.sample_identifier_verified],
        )
        auth_repo = get_auth_repo_with_user(user)
        data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_object = ConfirmationRequestObject.from_dict(data)
        use_case = TFAOldUserConfirmationSignInUseCase(
            auth_repo,
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
            MagicMock(),
        )
        result = use_case.execute(request_object).value.to_dict()
        refresh_token = result.get("refreshToken")
        auth_token = result.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # Confirming tokens are valid for MFA
        decoded_ref_token = self.token_adapter.verify_token(refresh_token, "refresh")
        self.assertEqual(
            Method.TWO_FACTOR_AUTH, decoded_ref_token[USER_CLAIMS_KEY]["method"]
        )
        decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
        self.assertEqual(
            decoded_auth_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND
        )

    def test_sign_in_user_on_confirmation_use_case__with_email_confirmation(self):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=True,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
        )
        auth_repo = get_auth_repo_with_user(user)
        data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_object = ConfirmationRequestObject.from_dict(data)
        use_case = EmailConfirmationSignInUseCase(
            auth_repo,
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
            MagicMock(),
        )
        result = use_case.execute(request_object).value.to_dict()
        refresh_token = result.get("refreshToken")
        auth_token = result.get("authToken")
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(auth_token)

        # Confirming tokens are not valid for MFA
        decoded_ref_token = self.token_adapter.verify_token(refresh_token, "refresh")
        self.assertEqual(
            Method.EMAIL_PASSWORD, decoded_ref_token[USER_CLAIMS_KEY]["method"]
        )
        decoded_auth_token = self.token_adapter.verify_token(auth_token, "access")
        self.assertIsNone(decoded_auth_token[USER_CLAIMS_KEY].get("validForMFA"))

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__valid_with_not_expirable_refresh_token(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        non_expirable_client = self.phoenix_config.server.project.clients[1]
        self.assertIsNone(non_expirable_client.refreshTokenExpiresAfterMinutes)

        # signin with email
        data = {
            SignInRequestObject.METHOD: Method.EMAIL,
            SignInRequestObject.EMAIL: USER_EMAIL,
            SignInRequestObject.CONFIRMATION_CODE: "123",
            SignInRequestObject.CLIENT_ID: non_expirable_client.clientId,
            SignInRequestObject.PROJECT_ID: "ptest1",
            SignInRequestObject.DEVICE_AGENT: "chrome",
        }
        request_data: SignInRequestObject = SignInRequestObject.from_dict(data)

        self._bind(auth_repo)

        use_case = sign_in_use_case_factory(request_data.method, request_data.authStage)
        result = use_case.execute(request_data).value.to_dict()
        self.assertIsNone(result["expiresIn"])
        post_sign_in_mock.assert_called_once_with(
            request_data, user, non_expirable_client
        )
        self.assertEqual(result["uid"], USER_ID)
        self.assertIn("refreshToken", result)

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__with_phone_number_not_adds_extra_identifiers(
        self, post_sign_in_mock
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        # signin with phone number
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.PHONE_NUMBER,
            phone_number=USER_PHONE_NUMBER,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        auth_repo.set_auth_attributes.assert_not_called()

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_sign_in__with_phone_number_adds_phone_number_identifier(
        self, post_sign_in_mock
    ):
        user = AuthUser(
            id=USER_ID, status=AuthUser.Status.NORMAL, phoneNumber=USER_PHONE_NUMBER
        )
        auth_repo = get_auth_repo_with_user(user)

        # signin with phone number
        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.PHONE_NUMBER,
            phone_number=USER_PHONE_NUMBER,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        correct_identifier = {
            AuthIdentifier.TYPE: AuthIdentifierType.PHONE_NUMBER,
            AuthIdentifier.VALUE: USER_PHONE_NUMBER,
            AuthIdentifier.VERIFIED: True,
        }

        auth_repo.set_auth_attributes.assert_called_once_with(
            USER_ID, mfa_identifiers=[correct_identifier]
        )

    def test_failure_email_confirmation_use_case(self):
        user = AuthUser(
            id=USER_ID,
            status=AuthUser.Status.NORMAL,
            email=USER_EMAIL,
            emailVerified=False,
            hashedPassword=USER_HASHED_PASSWORD_VALUE,
        )
        auth_repo = get_auth_repo_with_user(user)
        data = {
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: "123",
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_object = ConfirmationRequestObject.from_dict(data)
        use_case = EmailConfirmationSignInUseCase(
            auth_repo,
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
            MagicMock(),
        )

        with self.assertRaises(EmailNotVerifiedException):
            use_case.execute(request_object)

    @patch(POST_SIGN_IN_MOCK_PATH)
    def test_remember_me_duration(self, post_sign_in_mock):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        first_factor_token = prepare_first_factor_refresh_token(
            self.token_adapter, user.id
        )

        result, request_data = self.execute_sign_in_use_case(
            auth_repo=auth_repo,
            method=Method.TWO_FACTOR_AUTH,
            refresh_token=first_factor_token,
        )
        post_sign_in_mock.assert_called_once_with(
            request_data, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        mfa_refresh_token = result.get("refreshToken")
        self.assertIsNotNone(mfa_refresh_token)
        decoded_mfa_refresh_token = self.token_adapter.verify_token(
            mfa_refresh_token, "refresh"
        )
        self.assertIsNone(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY].get("secondFactorRequired")
        )
        self.assertEqual(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY]["method"], Method.TWO_FACTOR_AUTH
        )

        data = {
            SignInRequestObjectV1.METHOD: Method.TWO_FACTOR_AUTH,
            SignInRequestObjectV1.EMAIL: user.email,
            SignInRequestObjectV1.PASSWORD: user.hashedPassword,
            SignInRequestObjectV1.REFRESH_TOKEN: mfa_refresh_token,
            SignInRequestObjectV1.CLIENT_ID: "ctest1",
            SignInRequestObjectV1.PROJECT_ID: "ptest1",
            SignInRequestObjectV1.DEVICE_AGENT: "chrome",
        }
        request_object = SignInRequestObjectV1.from_dict(remove_none_values(data))

        self._bind(auth_repo)
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        result = use_case.execute(request_object).value.to_dict()

        post_sign_in_mock.assert_called_once_with(
            request_object, user, self.sample_client
        )
        post_sign_in_mock.reset_mock()
        self.assertEqual(result["uid"], USER_ID)
        mfa_refresh_token = result.get("refreshToken")
        self.assertIsNotNone(mfa_refresh_token)
        decoded_mfa_refresh_token = self.token_adapter.verify_token(
            mfa_refresh_token, "refresh"
        )
        self.assertIsNone(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY].get("secondFactorRequired")
        )
        self.assertEqual(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY]["method"], Method.TWO_FACTOR_AUTH
        )
        self.assertEqual(
            decoded_mfa_refresh_token[USER_CLAIMS_KEY]["authStage"], AuthStage.SECOND
        )

        data[SignInRequestObjectV1.REFRESH_TOKEN] = first_factor_token
        request_object = SignInRequestObjectV1.from_dict(remove_none_values(data))
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        with self.assertRaises(WrongTokenException):
            use_case.execute(request_object)

        wrong_factor_token = prepare_first_factor_refresh_token(
            self.token_adapter, user.id, Method.EMAIL
        )
        data[SignInRequestObjectV1.REFRESH_TOKEN] = wrong_factor_token
        request_object = SignInRequestObjectV1.from_dict(remove_none_values(data))
        use_case = sign_in_use_case_factory_v1(
            request_object.method, request_object.authStage
        )
        with self.assertRaises(InvalidTokenProviderException):
            use_case.execute(request_object)


class SignInSmsTestCase(BaseSignInTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.sms_adapter.code = "123123"

    def test_sign_in__test_env_phone_number(self):
        self.phoenix_config.server.testEnvironment = False
        user = filled_auth_user(mfa_phone_number=TEST_PHONE_NUMBER)
        user.phoneNumber = TEST_PHONE_NUMBER
        auth_repo = get_auth_repo_with_user(user)
        request_object = self._get_request_object(
            method=Method.PHONE_NUMBER,
            phone_number=TEST_PHONE_NUMBER,
            confirmation_code=TEST_CONFIRMATION_CODE,
        )
        # signin with phone number
        phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self._bind(auth_repo, self.token_adapter, phoenix_config)

        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )

        # confirming exception when not test env is used
        with self.assertRaises(InvalidVerificationCodeException):
            use_case.execute(request_object).value.to_dict()

        # confirming test credentials works when test env is used
        phoenix_config.server.testEnvironment = True
        use_case.execute(request_object).value.to_dict()

    def test_sign_in__test_env_mfa(self):
        self.phoenix_config.server.testEnvironment = False
        user = filled_auth_user(mfa_phone_number=TEST_PHONE_NUMBER)
        user.phoneNumber = TEST_PHONE_NUMBER
        auth_repo = get_auth_repo_with_user(user)

        first_factor_token = prepare_first_factor_refresh_token(
            self.token_adapter, user.id
        )

        request_object = self._get_request_object(
            method=Method.TWO_FACTOR_AUTH,
            refresh_token=first_factor_token,
            confirmation_code=TEST_CONFIRMATION_CODE,
        )

        phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        token_adapter = JwtTokenAdapter(JwtTokenConfig(secret="test"), phoenix_config)

        self._bind(auth_repo, token_adapter, phoenix_config)

        use_case = sign_in_use_case_factory(
            request_object.method, request_object.authStage
        )

        # confirming exception when not test env is used
        with self.assertRaises(InvalidVerificationCodeException):
            use_case.execute(request_object).value.to_dict()

        # confirming test credentials works when test env is used
        phoenix_config.server.testEnvironment = True
        use_case.execute(request_object).value.to_dict()

    def test_confirmation__test_env_phone_number(self):
        self.phoenix_config.server.testEnvironment = False
        user = filled_auth_user(
            mfa_phone_number=TEST_PHONE_NUMBER, identifier_verified=False
        )
        user.hashedPassword = None  # to avoid sign in
        auth_repo = get_auth_repo_with_user(user)

        data = {
            ConfirmationRequestObject.PHONE_NUMBER: TEST_PHONE_NUMBER,
            ConfirmationRequestObject.EMAIL: USER_EMAIL,
            ConfirmationRequestObject.CONFIRMATION_CODE: TEST_CONFIRMATION_CODE,
            ConfirmationRequestObject.CLIENT_ID: "ctest1",
            ConfirmationRequestObject.PROJECT_ID: "ptest1",
            ConfirmationRequestObject.DEVICE_AGENT: "chrome",
        }
        request_object = ConfirmationRequestObject.from_dict(data)

        use_case = ConfirmationUseCase(
            auth_repo,
            MagicMock(),
            self.phoenix_config,
            self.token_adapter,
            MagicMock(),
        )
        with self.assertRaises(InvalidVerificationCodeException):
            use_case.execute(request_object).value.to_dict()

        # confirming test credentials works when test env is used
        self.phoenix_config.server.testEnvironment = True
        use_case.execute(request_object).value.to_dict()
