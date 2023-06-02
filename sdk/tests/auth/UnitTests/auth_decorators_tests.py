import functools
import unittest
from unittest.mock import patch, MagicMock

from werkzeug.local import LocalStack

from sdk.auth.decorators import auth_required, AuthMethod
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.exceptions.exceptions import DetailedException
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import IDENTITY_CLAIM_KEY, USER_CLAIMS_KEY
from sdk.phoenix.config.server_config import PhoenixServerConfig, Project, Client

USER_ID = "x1"
PROJECT_ID = "p1"
CLIENT_ID = "c1"


def _jwt_claim():
    return {
        IDENTITY_CLAIM_KEY: USER_ID,
        USER_CLAIMS_KEY: {"projectId": PROJECT_ID, "clientId": CLIENT_ID},
    }


def _auth_method_type():
    return AuthMethod.JWT


@functools.lru_cache(1)
def _current_g():
    return LocalStack()


def _auth_user():
    return AuthUser(id=USER_ID, status=AuthUser.Status.NORMAL, email="m@mo.com")


def _auth_user_compromised():
    return AuthUser(id=USER_ID, status=AuthUser.Status.COMPROMISED, email="m@mo.com")


def _phoenix_config():
    server_config = MagicMock()
    server_config.server.project = Project(
        id=PROJECT_ID, clients=[Client(clientId=CLIENT_ID)]
    )
    return server_config


class AuthRequiredTestCase(unittest.TestCase):
    @patch("sdk.auth.decorators.get_authorization_method_type", _auth_method_type)
    @patch("sdk.auth.decorators.verify_jwt_in_request", _jwt_claim)
    @patch("sdk.auth.decorators.g", _current_g())
    def test_a_normal_user(self):
        auth_repo = MagicMock()
        auth_repo.get_user.return_value = _auth_user()

        def bind_and_configure(binder):
            binder.bind(AuthRepository, auth_repo)
            binder.bind(PhoenixServerConfig, _phoenix_config())

        inject.clear_and_configure(bind_and_configure)

        @auth_required()
        def fake_router():
            pass

        fake_router()

        self.assertEqual(_current_g().auth_user.id, _auth_user().id)
        self.assertEqual(_current_g().auth_user.email, _auth_user().email)

    @patch("sdk.auth.decorators.get_authorization_method_type", _auth_method_type)
    @patch("sdk.auth.decorators.verify_jwt_in_request", _jwt_claim)
    @patch("sdk.auth.decorators.g", _current_g())
    def test_compromised_user(self):
        auth_repo = MagicMock()
        auth_repo.get_user.return_value = _auth_user_compromised()

        def bind_and_configure(binder):
            binder.bind(AuthRepository, auth_repo)
            binder.bind(PhoenixServerConfig, _phoenix_config())

        inject.clear_and_configure(bind_and_configure)

        @auth_required()
        def fake_router():
            pass

        with self.assertRaises(DetailedException):
            fake_router()

    @patch("sdk.auth.decorators.get_authorization_method_type", _auth_method_type)
    @patch("sdk.auth.decorators.verify_jwt_in_request", _jwt_claim)
    @patch("sdk.auth.decorators.g", _current_g())
    def test_deleted_user(self):
        auth_repo = MagicMock()
        auth_repo.get_user.return_value = None

        def bind_and_configure(binder):
            binder.bind(AuthRepository, auth_repo)
            binder.bind(PhoenixServerConfig, _phoenix_config())

        inject.clear_and_configure(bind_and_configure)

        @auth_required()
        def fake_router():
            pass

        with self.assertRaises(DetailedException):
            fake_router()


if __name__ == "__main__":
    unittest.main()
