from unittest.mock import patch

from sdk.auth.decorators import auth_required
from sdk.common.adapter.sentry.sentry_adapter import SentryAdapter
from sdk.tests.auth.UnitTests.check_auth_tests import SAMPLE_USER_DATA
from sdk.tests.auth.test_helpers import USER_ID
from sdk.tests.test_case import SdkTestCase

SENTRY_PATH = "sdk.common.adapter.sentry.sentry_adapter"


class TestSentryAdapter(SentryAdapter):
    def is_configured(self) -> bool:
        return True


class SentryErrorLoggingTests(SdkTestCase):
    components = []

    @classmethod
    def setUpClass(cls) -> None:
        super(SentryErrorLoggingTests, cls).setUpClass()

        @cls.test_app.route("/ok")
        def success_route():
            return "ok", 200

        @cls.test_app.route("/protected")
        @auth_required()
        def protected_route():
            return "ok", 200

    @patch("sdk.auth.decorators.set_user")
    def test_user_not_logged(self, mocked_set_user):
        rsp = self.flask_client.get("/ok")
        self.assertEqual(200, rsp.status_code)
        mocked_set_user.assert_not_called()

    @patch("sdk.auth.decorators.set_user")
    def test_user_logged_during_authorized_request(self, mocked_set_user):
        headers = self.get_headers_for_token(USER_ID)
        self.flask_client.get("/protected", headers=headers)
        mocked_set_user.assert_called_once_with(SAMPLE_USER_DATA)
