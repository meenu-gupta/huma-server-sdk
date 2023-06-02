import unittest
from unittest.mock import MagicMock

from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.exceptions.exceptions import WrongTokenException


class JWTTokenAdapterTestCase(unittest.TestCase):
    def test_failure_verify_token_decode_exception(self):
        adapter = JwtTokenAdapter(MagicMock(), MagicMock())
        functions_to_test = [
            adapter.verify_invitation_token,
            adapter.verify_confirmation_token,
            adapter.verify_token,
        ]
        for function in functions_to_test:
            with self.assertRaises(WrongTokenException):
                function("wrong_jwt_token")


if __name__ == "__main__":
    unittest.main()
