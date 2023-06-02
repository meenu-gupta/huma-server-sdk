import unittest
from unittest.mock import patch, MagicMock

from sdk.auth.model.auth_user import AuthUser, AuthIdentifier, AuthIdentifierType
from sdk.auth.use_case.auth_request_objects import (
    CheckAuthAttributesRequestObject,
    SetAuthAttributesRequestObject,
)
from sdk.auth.use_case.auth_use_cases import (
    CheckAuthAttributesUseCase,
    SetAuthAttributesUseCase,
    verify_mfa_identifier,
)

from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenType
from sdk.common.exceptions.exceptions import (
    EmailAlreadySetException,
    PasswordAlreadySetException,
    UnauthorizedException,
    WrongTokenException,
    ConfirmationCodeIsMissing,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH
from sdk.tests.auth.UnitTests.base_auth_request_tests import BaseAuthTestCase
from sdk.tests.auth.test_helpers import (
    auth_user,
    filled_auth_user,
    get_auth_repo_with_user,
    USER_ID,
    USER_EMAIL,
    USER_PHONE_NUMBER,
    USER_PASSWORD,
    hashed_password_mock,
    USER_HASHED_PASSWORD_VALUE,
    NOT_EXISTING_EMAIL,
    TEST_CLIENT_ID,
    PROJECT_ID,
)

AUTH_USE_CASE_PATH = "sdk.auth.use_case.auth_use_cases"
SMS_FACTORY_PATH = f"{AUTH_USE_CASE_PATH}.SMSAdapterFactory"


class CheckAuthAttributesTestCase(BaseAuthTestCase):
    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), self.phoenix_config
        )

    def execute_check_auth_attributes_use_case(
        self, auth_repo, email=None, auth_token=None, phone_number=None, token_type=None
    ):
        data = {
            CheckAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            CheckAuthAttributesRequestObject.EMAIL: email,
            CheckAuthAttributesRequestObject.PHONE_NUMBER: phone_number,
            CheckAuthAttributesRequestObject.CLIENT_ID: TEST_CLIENT_ID,
            CheckAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
            CheckAuthAttributesRequestObject.TOKEN_TYPE: token_type,
        }
        request_data = CheckAuthAttributesRequestObject.from_dict(
            remove_none_values(data)
        )
        resp = CheckAuthAttributesUseCase(
            auth_repo, self.token_adapter, MagicMock(), self.phoenix_config
        ).execute(request_data)
        return resp.value.to_dict()

    def test_check_auth_attributes_use_case__unfilled_user(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, auth_token=token
        )

        self.assertEqual(result["email"], USER_EMAIL)
        self.assertEqual(result["emailVerified"], False)
        self.assertIsNone(result["phoneNumber"])
        self.assertEqual(result["passwordSet"], False)
        self.assertEqual(result["phoneNumberVerified"], False)
        self.assertEqual(result["eligibleForMFA"], False)

    def test_check_auth_attributes_use_case__filled_user(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, auth_token=token
        )

        self.assertEqual(result["email"], USER_EMAIL)
        self.assertEqual(result["emailVerified"], True)
        self.assertEqual(result["phoneNumber"], USER_PHONE_NUMBER)
        self.assertEqual(result["passwordSet"], True)
        self.assertEqual(result["phoneNumberVerified"], True)
        self.assertEqual(result["eligibleForMFA"], True)

    def test_check_auth_attributes_use_case__email_only_filled_user(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, email=USER_EMAIL
        )

        self.assertEqual(7, len(result))
        self.assertEqual(result["email"], USER_EMAIL)
        self.assertTrue(result["eligibleForMFA"])
        self.assertTrue(result["passwordSet"])
        self.assertIsNone(result["emailVerified"])
        self.assertIsNone(result["phoneNumber"])
        self.assertIsNone(result["phoneNumberVerified"])
        self.assertIsNone(result["mfaEnabled"])

    def test_check_auth_attributes_use_case__email_only_not_filled_user(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, email=USER_EMAIL
        )

        self.assertEqual(7, len(result))
        self.assertEqual(result["email"], USER_EMAIL)
        self.assertFalse(result["eligibleForMFA"])
        self.assertFalse(result["passwordSet"])

        self.assertIsNone(result["emailVerified"])
        self.assertIsNone(result["phoneNumber"])
        self.assertIsNone(result["phoneNumberVerified"])
        self.assertIsNone(result["mfaEnabled"])

    def test_check_auth_attributes_use_case__phone_number_only_filled_user(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, phone_number=USER_PHONE_NUMBER
        )

        self.assertEqual(7, len(result))
        self.assertEqual(result["email"], USER_EMAIL)
        self.assertTrue(result["eligibleForMFA"])
        self.assertTrue(result["passwordSet"])

        self.assertIsNone(result["emailVerified"])
        self.assertIsNone(result["phoneNumber"])
        self.assertIsNone(result["phoneNumberVerified"])
        self.assertIsNone(result["mfaEnabled"])

    def test_check_auth_attributes_use_case__raises_user_not_exist(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)

        with self.assertRaises(UnauthorizedException):
            self.execute_check_auth_attributes_use_case(
                auth_repo, email="somerandommail@gmail.com"
            )

        with self.assertRaises(UnauthorizedException):
            self.execute_check_auth_attributes_use_case(
                auth_repo, phone_number="+380500000000"
            )

    def test_check_auth_attributes_use_case__invitation_token(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_token(
            user.id, TokenType.INVITATION.string_value
        )

        result = self.execute_check_auth_attributes_use_case(
            auth_repo, auth_token=token, token_type=TokenType.INVITATION.string_value
        )

        self.assertEqual(result["email"], USER_EMAIL)
        self.assertEqual(result["emailVerified"], False)
        self.assertIsNone(result["phoneNumber"])
        self.assertEqual(result["passwordSet"], False)
        self.assertEqual(result["phoneNumberVerified"], False)
        self.assertEqual(result["eligibleForMFA"], False)


class SetAuthAttributesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.event_bus_mocked = MagicMock()
        self.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), self.phoenix_config
        )
        self.sample_identifier = AuthIdentifier(
            type=AuthIdentifierType.PHONE_NUMBER,
            value=USER_PHONE_NUMBER,
        )

    def execute_set_auth_attributes_use_case(
        self,
        repo,
        auth_token,
        phone_number=None,
        email=None,
        password=None,
        mfa_enabled=None,
        token_type=None,
        confirmation_code=None,
    ):
        data = {
            SetAuthAttributesRequestObject.AUTH_TOKEN: auth_token,
            SetAuthAttributesRequestObject.PHONE_NUMBER: phone_number,
            SetAuthAttributesRequestObject.EMAIL: email,
            SetAuthAttributesRequestObject.PASSWORD: password,
            SetAuthAttributesRequestObject.MFA_ENABLED: mfa_enabled,
            SetAuthAttributesRequestObject.CLIENT_ID: TEST_CLIENT_ID,
            SetAuthAttributesRequestObject.PROJECT_ID: PROJECT_ID,
            SetAuthAttributesRequestObject.TOKEN_TYPE: token_type,
            SetAuthAttributesRequestObject.CONFIRMATION_CODE: confirmation_code,
        }
        request_obj = SetAuthAttributesRequestObject.from_dict(remove_none_values(data))
        use_case = SetAuthAttributesUseCase(
            repo, self.token_adapter, self.event_bus_mocked, self.phoenix_config
        )
        resp = use_case.execute(request_obj)
        return resp.value.to_dict()

    def test_set_auth_attributes_use_case__email_second_time_forbidden(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        with self.assertRaises(EmailAlreadySetException):
            self.execute_set_auth_attributes_use_case(
                auth_repo, auth_token=token, email=USER_EMAIL
            )

    @patch(SMS_FACTORY_PATH, MagicMock())
    @patch(f"{AUTH_USE_CASE_PATH}.validate_phone_number_code")
    def test_set_auth_attributes_use_case__phone_number_second_time_allowed(
        self, validate_phone_number
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)
        confirmation_code = "111"
        new_phone_number = "+441347722096"

        self.execute_set_auth_attributes_use_case(
            auth_repo,
            auth_token=token,
            phone_number=new_phone_number,
            confirmation_code=confirmation_code,
        )
        identifier = {
            **self.sample_identifier.to_dict(),
            AuthIdentifier.VALUE: new_phone_number,
            AuthIdentifier.VERIFIED: True,
        }
        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            mfa_identifiers=[identifier],
        )
        validate_phone_number.assert_called_with(
            self.phoenix_config, new_phone_number, confirmation_code
        )

    @patch(SMS_FACTORY_PATH, MagicMock())
    def test_failure_set_auth_attributes_use_case__phone_number_second_time_no_confirmation_code(
        self,
    ):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        with self.assertRaises(ConfirmationCodeIsMissing):
            self.execute_set_auth_attributes_use_case(
                auth_repo, auth_token=token, phone_number=USER_PHONE_NUMBER
            )

    def test_set_auth_attributes_use_case__phone_number_not_verified_second_time_allowed(
        self,
    ):
        user = filled_auth_user(identifier_verified=False)
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_set_auth_attributes_use_case(
            auth_repo, auth_token=token, phone_number=USER_PHONE_NUMBER
        )

        self.assertEqual(result["uid"], USER_ID)
        identifier_data = self.sample_identifier.to_dict()
        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            mfa_identifiers=[identifier_data],
        )

    def test_set_auth_attributes_use_case__password_second_time_forbidden(self):
        user = filled_auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        with self.assertRaises(PasswordAlreadySetException):
            self.execute_set_auth_attributes_use_case(
                auth_repo, token, password=USER_PASSWORD
            )

    @patch("sdk.auth.use_case.auth_use_cases.hash_new_password", hashed_password_mock)
    def test_set_auth_attributes_use_case__phone_number(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_set_auth_attributes_use_case(
            auth_repo, token, phone_number=USER_PHONE_NUMBER, password=USER_PASSWORD
        )
        self.assertEqual(result["uid"], USER_ID)

        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            password=USER_HASHED_PASSWORD_VALUE,
            mfa_identifiers=[self.sample_identifier.to_dict()],
        )

    @patch("sdk.auth.use_case.auth_use_cases.hash_new_password", hashed_password_mock)
    def test_set_auth_attributes_use_case__email(self):
        user = AuthUser(
            id=USER_ID, status=AuthUser.Status.NORMAL, phoneNumber=USER_PHONE_NUMBER
        )
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_set_auth_attributes_use_case(
            auth_repo, token, email=NOT_EXISTING_EMAIL, password=USER_PASSWORD
        )
        self.assertEqual(result["uid"], USER_ID)

        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            password=USER_HASHED_PASSWORD_VALUE,
            email=NOT_EXISTING_EMAIL,
        )

    @patch("sdk.auth.use_case.auth_use_cases.hash_new_password", hashed_password_mock)
    def test_set_auth_attributes_use_case__mfa_enabled(self):
        user = AuthUser(
            id=USER_ID, status=AuthUser.Status.NORMAL, phoneNumber=USER_PHONE_NUMBER
        )
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_access_token(user.id)

        result = self.execute_set_auth_attributes_use_case(
            auth_repo, token, mfa_enabled=False
        )
        self.assertEqual(result["uid"], USER_ID)

        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            mfa_enabled=False,
        )

    @patch("sdk.auth.use_case.auth_use_cases.hash_new_password", hashed_password_mock)
    def test_set_auth_attributes_use_case__invitation_token(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_token(
            user.id, TokenType.INVITATION.string_value
        )

        result = self.execute_set_auth_attributes_use_case(
            repo=auth_repo,
            auth_token=token,
            password=USER_PASSWORD,
            token_type=TokenType.INVITATION.string_value,
        )

        auth_repo.set_auth_attributes.assert_called_with(
            USER_ID,
            password=USER_HASHED_PASSWORD_VALUE,
        )
        self.assertEqual(result["uid"], USER_ID)

    def test_set_auth_attributes_use_case__failure_on_wrong_token_type(self):
        user = auth_user()
        auth_repo = get_auth_repo_with_user(user)
        token = self.token_adapter.create_token(
            user.id, TokenType.INVITATION.string_value
        )

        # failure during submitting invitation token with access type
        with self.assertRaises(WrongTokenException):
            self.execute_set_auth_attributes_use_case(
                repo=auth_repo,
                auth_token=token,
                password=USER_PASSWORD,
                token_type=TokenType.ACCESS.string_value,
            )


class AuthIdentifierTests(unittest.TestCase):
    def test_has_mfa_identifier_valid(self):
        test_type = AuthIdentifierType.PHONE_NUMBER
        identifier = AuthIdentifier(
            type=test_type,
            value=USER_PHONE_NUMBER,
        )
        user = AuthUser(id=USER_ID, mfaIdentifiers=[identifier])
        self.assertTrue(user.has_mfa_identifier(test_type))
        self.assertFalse(user.has_mfa_identifier_verified(test_type))

    def test_get_mfa_identifier_returns_none(self):
        test_type = AuthIdentifierType.PHONE_NUMBER

        user = AuthUser(id=USER_ID, mfaIdentifiers=[])
        self.assertIsNone(user.get_mfa_identifier(test_type))

        user = AuthUser(id=USER_ID)
        self.assertIsNone(user.get_mfa_identifier(test_type))

    def test_get_mfa_identifier_valid(self):
        test_type = AuthIdentifierType.PHONE_NUMBER
        test_value = "+380500000000"
        identifier = AuthIdentifier(
            type=test_type,
            value=test_value,
        )

        user = AuthUser(id=USER_ID, mfaIdentifiers=[identifier])
        user_identifier = user.get_mfa_identifier(test_type)
        self.assertEqual(user_identifier, identifier)

    def test_add_identifier_to_list(self):
        test_type = AuthIdentifierType.PHONE_NUMBER
        user = AuthUser(id=USER_ID)
        self.assertFalse(user.has_mfa_identifier(test_type))

        user.add_mfa_identifier(test_type, USER_PHONE_NUMBER)
        self.assertTrue(user.has_mfa_identifier(test_type))

    def test_verify_mfa_identifier_valid(self):
        auth_repo_mock = MagicMock()
        test_type = AuthIdentifierType.PHONE_NUMBER
        identifier = AuthIdentifier(
            type=test_type,
            value=USER_PHONE_NUMBER,
        )
        verified_identifier = AuthIdentifier(
            type=test_type, value=USER_PHONE_NUMBER, verified=True
        )
        user = AuthUser(id=USER_ID, mfaIdentifiers=[identifier])
        verify_mfa_identifier(user, test_type, auth_repo_mock)
        auth_repo_mock.set_auth_attributes.assert_called_with(
            user.id, mfa_identifiers=[verified_identifier.to_dict()]
        )


if __name__ == "__main__":
    unittest.main()
