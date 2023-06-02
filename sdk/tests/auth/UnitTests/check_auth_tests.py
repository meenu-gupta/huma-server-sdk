import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from sdk.auth.decorators import check_auth
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import BaseAuthRequestObject
from sdk.common.adapter.sentry.sentry_adapter import SentryAdapter
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.tests.auth.test_helpers import USER_ID, USER_EMAIL
from sdk.tests.constants import PROJECT_ID, CLIENT_ID
from sdk.tests.phoenix.UnitTests.bind_tests import get_config

SAMPLE_USER_DATA = {SentryAdapter.USER_ID: USER_ID}


class CheckAuthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        test_app = Flask(__name__)
        mocked_auth_repo = MagicMock()
        mocked_auth_repo.get_user.return_value = AuthUser(
            id=USER_ID, status=AuthUser.Status.NORMAL, email=USER_EMAIL
        )

        token_adapter = JwtTokenAdapter(JwtTokenConfig(secret="test"), MagicMock())
        claims = {
            BaseAuthRequestObject.PROJECT_ID: PROJECT_ID,
            BaseAuthRequestObject.CLIENT_ID: CLIENT_ID,
        }
        token = token_adapter.create_access_token(USER_ID, claims)

        headers_data = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        self.context = test_app.test_request_context(environ_base=headers_data)
        self.context.push()

        def bind(binder):
            binder.bind(PhoenixServerConfig, get_config())
            binder.bind(TokenAdapter, token_adapter)
            binder.bind(AuthRepository, mocked_auth_repo)

        inject.clear_and_configure(bind)

    def tearDown(self) -> None:
        self.context.pop()

    def test_check_auth_logs_sentry_user(self):
        with patch("sdk.auth.decorators.set_user") as mock_set:
            check_auth()
        mock_set.assert_called_once_with(SAMPLE_USER_DATA)
