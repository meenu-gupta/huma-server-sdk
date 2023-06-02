from unittest import TestCase
from unittest.mock import MagicMock, patch

from bson import ObjectId
from flask import g, Flask

from extensions.authorization.callbacks import (
    on_token_extraction_callback,
    TokenExtractionEvent,
    extract_user,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from sdk.common.utils import inject
from sdk.tests.auth.test_helpers import USER_EMAIL, USER_ID

AUTHZ_PATH = "extensions.authorization"


class MockService:
    roles = [RoleAssignment(roleId=RoleName.USER, resource="deployment/*")]
    retrieve_simple_user_profile = MagicMock()
    retrieve_simple_user_profile.return_value = User(roles=roles)
    retrieve_user_profile = MagicMock()
    retrieve_user_profile.return_value = User(roles=roles)


class FlaskGTests(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        inject.clear_and_configure(
            lambda binder: binder.bind(DefaultRoles, DefaultRoles())
        )

    @patch(f"{AUTHZ_PATH}.callbacks.callbacks.AuthorizationService", MockService)
    @patch(f"{AUTHZ_PATH}.middleware.authorization.AuthorizationService", MockService)
    def test_auth_on_token_extraction_callback(self):
        with self.app.test_request_context():
            self.assertEqual(len(g.__dict__.keys()), 0)
            event = TokenExtractionEvent(id=USER_ID, email=USER_EMAIL)
            on_token_extraction_callback(event)
            self.assertEqual(type(g.authz_user), AuthorizedUser)
            self.assertEqual(type(g.user), User)

    @patch(f"{AUTHZ_PATH}.callbacks.callbacks.AuthorizationService")
    def test_extract_user_valid(self, mocked_service):
        with self.app.test_request_context():
            g.user = User(id=USER_ID)
            # confirming not called extraction from service cause id is same as in global
            extract_user(user_id=USER_ID)
            mocked_service().retrieve_user_profile.assert_not_called()

            # extracting user from db cause id is not same as global user's
            extract_user(user_id=str(ObjectId()))
            mocked_service().retrieve_user_profile.assert_called_once()
