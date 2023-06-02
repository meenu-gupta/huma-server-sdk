import datetime
import unittest
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from sdk.auth.enums import AuthStage
from sdk.auth.model.session import DeviceSession
from sdk.auth.use_case.auth_request_objects import (
    Method,
    RefreshTokenRequestObject,
    RefreshTokenRequestObjectV1,
)
from sdk.auth.use_case.auth_use_cases import RefreshTokenUseCase, RefreshTokenUseCaseV1
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.exceptions.exceptions import (
    DetailedException,
    ErrorCodes,
    InvalidUsernameOrPasswordException,
)
from sdk.common.utils.token.jwt.jwt import USER_CLAIMS_KEY, AUTH_STAGE
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH


from sdk.tests.auth.test_helpers import (
    filled_auth_user,
    get_auth_repo_with_user,
    USER_ID,
    USER_PASSWORD,
    USER_EMAIL,
)

DEVICE_AGENT = "chrome"


class RefreshTokenTestCase(unittest.TestCase):
    EXPIRES_IN_MINUTES = 2880

    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), self.phoenix_config
        )
        self.user = filled_auth_user()

    def _get_mfa_refresh_token(self, claims: dict = None, expires_in: int = None):
        if expires_in:
            expires_in = datetime.timedelta(minutes=expires_in)
        default_claims = {
            "clientId": "ctest1",
            "projectId": "ptest1",
            "method": Method.TWO_FACTOR_AUTH,
            AUTH_STAGE: AuthStage.SECOND,
        }
        claims = claims or default_claims
        return self.token_adapter.create_refresh_token(
            USER_ID,
            user_claims=claims,
            expires_delta=expires_in,
        )

    def _get_refresh_token_use_case(self):
        auth_repo = get_auth_repo_with_user(self.user)
        session = DeviceSession(userId=self.user.id, deviceAgent=DEVICE_AGENT)
        auth_repo.retrieve_device_session.return_value = session
        return RefreshTokenUseCaseV1(auth_repo, self.phoenix_config, self.token_adapter)

    def test_mfa_refresh_token_use_case__mfa_token_valid(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES
        )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        resp = use_case.execute(request_data).value
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        self.assertEqual(access_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND)

    def test_mfa_refresh_token__sfa_token_not_valid(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        methods = [Method.EMAIL, Method.EMAIL_PASSWORD, Method.PHONE_NUMBER]
        for auth_method in methods:
            claims = {
                "clientId": "ctest1",
                "projectId": "ptest1",
                "method": auth_method,
                AUTH_STAGE: AuthStage.NORMAL,
            }
            method_refresh_token = self.token_adapter.create_refresh_token(
                USER_ID, user_claims=claims
            )

            data = {
                RefreshTokenRequestObject.REFRESH_TOKEN: method_refresh_token,
                RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
                RefreshTokenRequestObject.EMAIL: USER_EMAIL,
                RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
            }

            request_data = RefreshTokenRequestObject.from_dict(data)
            use_case = RefreshTokenUseCase(
                auth_repo, self.phoenix_config, self.token_adapter
            )
            resp = use_case.execute(request_data).value
            access_token = self.token_adapter.verify_token(resp.authToken, "access")
            self.assertIsNone(access_token[USER_CLAIMS_KEY].get("validForMFA"))

    def test_mfa_refresh_token__timeout_returns_new_refresh_token(self):
        """
        This test is used to confirm that new refresh token is issued during refreshing
        in period between expiration of access token and own expiration
        """

        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        now = datetime.datetime.utcnow()
        # NOTE: token will be expired after expiration date
        # at expiration date, it is still valid, but session is expired
        expiration_date = now + relativedelta(minutes=self.EXPIRES_IN_MINUTES)

        with freeze_time(now):
            refresh_token_mfa = self._get_mfa_refresh_token(
                expires_in=self.EXPIRES_IN_MINUTES
            )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_mfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        with freeze_time(expiration_date):
            resp = use_case.execute(request_data).value
        new_refresh_token = resp.refreshToken
        self.assertNotEqual(new_refresh_token, refresh_token_mfa)

    def test_refresh_token__expired_raises_error(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        with freeze_time(
            datetime.datetime.utcnow()
            - relativedelta(minutes=self.EXPIRES_IN_MINUTES + 1)
        ):
            refresh_token_mfa = self._get_mfa_refresh_token(
                expires_in=self.EXPIRES_IN_MINUTES
            )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_mfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        with self.assertRaises(DetailedException) as use_case_exception:
            use_case.execute(request_data)
        self.assertEqual(use_case_exception.exception.code, ErrorCodes.TOKEN_EXPIRED)

    def test_mfa_refresh_token__returns_new_refresh_token(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        refresh_token_mfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES
        )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_mfa,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        resp = use_case.execute(request_data).value
        new_refresh_token = resp.refreshToken
        self.assertNotEqual(new_refresh_token, refresh_token_mfa)

    def test_refresh_token_not_expirable(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        refresh_token_tfa = self._get_mfa_refresh_token(expires_in=None)

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        resp = use_case.execute(request_data).value
        self.assertIsNone(resp.refreshTokenExpiresIn)

    def test_mfa_refresh_token_use_case__mfa_token_valid_with_old_logic(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        claims = {
            "clientId": "ctest1",
            "projectId": "ptest1",
            "method": Method.TWO_FACTOR_AUTH,
        }
        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES, claims=claims
        )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        resp = use_case.execute(request_data).value
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        # asserting stage is still second even it wasn't provided in claims
        stage = access_token[USER_CLAIMS_KEY].get(AUTH_STAGE)
        self.assertEqual(stage, AuthStage.SECOND)
        method = access_token[USER_CLAIMS_KEY].get("method")
        self.assertEqual(method, Method.TWO_FACTOR_AUTH)
        self.assertTrue(access_token[USER_CLAIMS_KEY].get("validForMFA"))

    def test_sfa_refresh_token_use_case__mfa_token_not_returned_with_old_logic(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        claims = {
            "clientId": "ctest1",
            "projectId": "ptest1",
            "method": Method.EMAIL,
        }
        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES, claims=claims
        )

        data = {
            RefreshTokenRequestObject.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObject.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObject.EMAIL: USER_EMAIL,
            RefreshTokenRequestObject.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObject.from_dict(data)
        use_case = RefreshTokenUseCase(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        resp = use_case.execute(request_data).value
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        # asserting stage is still second even it wasn't provided in claims
        stage = access_token[USER_CLAIMS_KEY].get(AUTH_STAGE)
        self.assertIsNone(stage)
        method = access_token[USER_CLAIMS_KEY].get("method")
        self.assertEqual(method, Method.EMAIL)
        self.assertFalse(access_token[USER_CLAIMS_KEY].get("validForMFA"))

    @patch("sdk.auth.use_case.auth_use_cases.update_current_session_v1")
    def test_mfa_refresh_token_use_case__v1_does_not_updates_session_with_device_token(
        self, mocked_update_session
    ):
        use_case = self._get_refresh_token_use_case()
        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES
        )

        data = {
            RefreshTokenRequestObjectV1.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObjectV1.DEVICE_TOKEN: "device token",
            RefreshTokenRequestObjectV1.DEVICE_AGENT: DEVICE_AGENT,
        }

        request_data = RefreshTokenRequestObjectV1.from_dict(data)
        resp = use_case.execute(request_data).value
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        self.assertEqual(access_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND)
        mocked_update_session.assert_not_called()

    @patch("sdk.auth.use_case.auth_use_cases.update_current_session_v1")
    def test_mfa_refresh_token_use_case__v1_updates_session_with_password(
        self, mocked_update_session
    ):
        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES
        )
        use_case = self._get_refresh_token_use_case()
        data = {
            RefreshTokenRequestObjectV1.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObjectV1.PASSWORD: "Test@123",
            RefreshTokenRequestObjectV1.DEVICE_AGENT: DEVICE_AGENT,
        }
        request_data = RefreshTokenRequestObjectV1.from_dict(data)
        resp = use_case.execute(request_data).value
        updated_refresh_token = resp.refreshToken
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        self.assertEqual(access_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND)
        mocked_update_session.assert_called_with(
            self.user.id,
            DEVICE_AGENT,
            use_case._repo,
            refresh_token_tfa,
            updated_refresh_token,
        )

    @patch("sdk.auth.use_case.auth_use_cases.update_current_session_v1")
    def test_mfa_refresh_token_use_case__v1_updates_session_without_password(
        self, mocked_update_session
    ):
        refresh_token_tfa = self._get_mfa_refresh_token(
            expires_in=self.EXPIRES_IN_MINUTES
        )
        use_case = self._get_refresh_token_use_case()
        data = {
            RefreshTokenRequestObjectV1.REFRESH_TOKEN: refresh_token_tfa,
            RefreshTokenRequestObjectV1.DEVICE_AGENT: DEVICE_AGENT,
        }
        request_data = RefreshTokenRequestObjectV1.from_dict(data)
        resp = use_case.execute(request_data).value
        updated_refresh_token = resp.refreshToken
        access_token = self.token_adapter.verify_token(resp.authToken, "access")
        self.assertEqual(access_token[USER_CLAIMS_KEY][AUTH_STAGE], AuthStage.SECOND)
        mocked_update_session.assert_called_with(
            self.user.id,
            DEVICE_AGENT,
            use_case._repo,
            refresh_token_tfa,
            updated_refresh_token,
        )

    def test_failure_refresh_token_with_email_and_password(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        claims = {
            "clientId": "ctest1",
            "projectId": "ptest1",
            "method": Method.EMAIL_PASSWORD,
            AUTH_STAGE: AuthStage.NORMAL,
        }
        method_refresh_token = self.token_adapter.create_refresh_token(
            USER_ID, user_claims=claims
        )

        data = {
            RefreshTokenRequestObjectV1.REFRESH_TOKEN: method_refresh_token,
            RefreshTokenRequestObjectV1.PASSWORD: USER_PASSWORD,
            RefreshTokenRequestObjectV1.EMAIL: USER_EMAIL,
            RefreshTokenRequestObjectV1.DEVICE_AGENT: "chrome",
        }

        request_data = RefreshTokenRequestObjectV1.from_dict(data)
        auth_repo.validate_password = MagicMock(return_value=False)
        use_case = RefreshTokenUseCaseV1(
            auth_repo, self.phoenix_config, self.token_adapter
        )
        with self.assertRaises(InvalidUsernameOrPasswordException):
            use_case.execute(request_data)
