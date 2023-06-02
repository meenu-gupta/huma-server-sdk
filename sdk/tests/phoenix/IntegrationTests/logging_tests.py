from unittest.mock import MagicMock

from sdk.common.adapter.monitoring_adapter import MonitoringAdapter
from sdk.common.exceptions.exceptions import DetailedException, ErrorCodes
from sdk.common.utils import inject
from sdk.tests.test_case import SdkTestCase

INFO_ERROR_CODES = {
    ErrorCodes.DUPLICATED_USER_ID,
    ErrorCodes.INVALID_EMAIL_CONFIRMATION_CODE,
    ErrorCodes.INVALID_VERIFICATION_CODE,
    ErrorCodes.INVITATION_CODE_EXPIRED,
    ErrorCodes.INVALID_USERNAME_OR_PASSWORD,
    ErrorCodes.PASSWORD_EXPIRED,
    ErrorCodes.SESSION_TIMEOUT,
    ErrorCodes.TOKEN_EXPIRED,
    ErrorCodes.UPDATE_REQUIRED,
    ErrorCodes.UNAUTHORIZED,
}

INFO_STATUS_CODES = {412, 428, 429}


class MockLogger:
    instance = MagicMock()
    log = MagicMock()


class TestMonitoringAdapter(MonitoringAdapter):
    report_exception = MagicMock()

    def is_configured(self) -> bool:
        return True


class ErrorLoggingTests(SdkTestCase):
    components = []

    @classmethod
    def setUpClass(cls) -> None:
        super(ErrorLoggingTests, cls).setUpClass()

        @cls.test_app.route("/success_route")
        def success_route():
            return "OK", 200

        @cls.test_app.route("/failure_route/<status_code>/<error_code>")
        def failure_route(status_code, error_code):
            raise DetailedException(int(error_code), "Failure", int(status_code))

    def setUp(self):
        super(ErrorLoggingTests, self).setUp()

        def bind(binder):
            TestMonitoringAdapter.report_exception.reset_mock()
            binder.bind(MonitoringAdapter, TestMonitoringAdapter())

        inject.clear_and_configure(bind)

    def test_success_request_not_logged(self):
        self.flask_client.get("/success_route")
        TestMonitoringAdapter.report_exception.assert_not_called()

    def test_failure_request_with_muted_status_codes_not_called(self):
        for status_code in INFO_STATUS_CODES:
            self.flask_client.get(f"/failure_route/{status_code}/100001")
            TestMonitoringAdapter.report_exception.assert_not_called()

    def test_failure_request_with_muted_error_codes_not_called(self):
        for error_code in INFO_ERROR_CODES:
            self.flask_client.get(f"/failure_route/400/{error_code}")
            TestMonitoringAdapter.report_exception.assert_not_called()

    def test_failure_request_logged(self):
        self.flask_client.get("/failure_route/400/400001")
        TestMonitoringAdapter.report_exception.assert_called_once()
