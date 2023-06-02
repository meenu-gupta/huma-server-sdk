import unittest
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenType
from sdk.common.exceptions.exceptions import WrongTokenException

from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH


class SetAuthAttributesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.phoenix_config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.token_adapter = JwtTokenAdapter(
            JwtTokenConfig(secret="test"), self.phoenix_config
        )

    def test_verify_token_failure(self) -> None:
        user_id = "5e8f0c74b50aa9656c34789c"

        token = self.token_adapter.create_access_token(user_id)

        with self.assertRaises(WrongTokenException):
            self.token_adapter.verify_token(
                token=token, request_type=TokenType.INVITATION.string_value
            )

    def test_verify_token_success(self):
        user_id = "5e8f0c74b50aa9656c34789c"

        token = self.token_adapter.create_refresh_token(user_id)

        result = self.token_adapter.verify_token(
            token=token, request_type=TokenType.REFRESH.string_value
        )

        self.assertEqual(result["identity"], user_id)
        self.assertEqual(result["type"], TokenType.REFRESH.string_value)
