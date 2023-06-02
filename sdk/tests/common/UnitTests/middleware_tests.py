import logging
from http import HTTPStatus
from unittest import TestCase
from unittest.mock import patch, MagicMock

from flask import Request, Flask, Response

from sdk.common.exceptions.exceptions import ErrorCodes, DetailedException
from sdk.common.logging.middleware import RequestErrorHandlerMiddleware
from sdk.common.utils import inject

test_app = Flask(__name__)

REQUEST_ID_KEY = RequestErrorHandlerMiddleware.X_REQUEST_ID_HEADER_KEY


class RequestErrorHandlerMiddlewareTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if inject.is_configured():
            inject.clear_and_configure()

    def test_request_id_default(self):
        request = Request.from_values(headers={})
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)
        self.assertIsNotNone(middleware.request_id)
        self.assertEqual(32, len(middleware.request_id))

    def test_add_warn_error_code(self):
        test_code = 1242323
        RequestErrorHandlerMiddleware.warn_error_code(test_code)
        self.assertIn(test_code, RequestErrorHandlerMiddleware.WARN_ERROR_CODES)

    def test_add_ignore_error_code(self):
        test_code = 1242323
        RequestErrorHandlerMiddleware.ignore_error_code(test_code)
        self.assertIn(test_code, RequestErrorHandlerMiddleware.INFO_ERROR_CODES)

    def test_skip_error_log_true(self):
        with test_app.app_context() as context:
            context.g.is_automation_request = True
            self.assertTrue(RequestErrorHandlerMiddleware.skip_error_log())

    def test_skip_error_log_false(self):
        with test_app.app_context() as context:
            context.g.is_automation_request = False
            self.assertFalse(RequestErrorHandlerMiddleware.skip_error_log())

    def test_skip_error_log_false_not_available_data(self):
        with test_app.app_context():
            self.assertFalse(RequestErrorHandlerMiddleware.skip_error_log())

    def test_skip_error_log_false_on_error(self):
        self.assertFalse(RequestErrorHandlerMiddleware.skip_error_log())

    @patch("sdk.common.logging.middleware.logger")
    @patch("sdk.common.logging.middleware.dump_request")
    def test_before_request(self, dump_request, logger):
        mock_request_id = "12345678"
        headers = {
            RequestErrorHandlerMiddleware.X_REQUEST_ID_HEADER_KEY: mock_request_id
        }
        request = Request.from_values(headers=headers)
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)
        self.assertEqual(mock_request_id, middleware.request_id)
        middleware.before_request(request)
        dump_request.assert_called_once_with(mock_request_id, request)
        logger.debug.assert_called_once()

    @patch("sdk.common.logging.middleware.logger")
    @patch("sdk.common.logging.middleware.dump_response")
    @patch("sdk.common.logging.middleware.dump_request")
    def test_after_request(self, dump_request, dump_response, logger):
        mock_request_id = "12345678"
        headers = {REQUEST_ID_KEY: mock_request_id}
        request = Request.from_values(headers=headers)
        response = Response(status=HTTPStatus.BAD_REQUEST)
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)

        self.assertEqual(mock_request_id, middleware.request_id)
        self.assertFalse(response.direct_passthrough)
        middleware.after_request(response)
        self.assertEqual(mock_request_id, response.headers[REQUEST_ID_KEY])
        dump_request.assert_called_once_with(mock_request_id, request)
        dump_response.assert_called_once_with(mock_request_id, response)
        self.assertEqual(2, logger.log.call_count)

    @patch("sdk.common.logging.middleware.logger")
    @patch("sdk.common.logging.middleware.dump_response")
    @patch("sdk.common.logging.middleware.dump_request")
    def test_after_request_200(self, dump_request, dump_response, logger):
        mock_request_id = "12345678"
        headers = {REQUEST_ID_KEY: mock_request_id}
        request = Request.from_values(headers=headers)
        response = Response(status=HTTPStatus.OK)
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)

        self.assertEqual(mock_request_id, middleware.request_id)
        self.assertFalse(response.direct_passthrough)
        middleware.after_request(response)
        self.assertEqual(mock_request_id, response.headers[REQUEST_ID_KEY])
        dump_request.assert_not_called()
        dump_response.assert_not_called()
        logger.log.assert_not_called()

    @patch("sdk.common.logging.middleware.report_exception")
    @patch("sdk.common.logging.middleware.logger")
    def test_handle_exception(self, logger, report_exception):
        request = MagicMock()
        exception = DetailedException(
            code=123456, debug_message="Test", status_code=401
        )
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)

        rsp, status_code = middleware.handle_exception(exception)
        report_exception.assert_called_once()
        logger.log.assert_not_called()
        self.assertDictEqual({"code": 123456, "message": "Test"}, rsp)

    @patch("sdk.common.logging.middleware.report_exception")
    @patch("sdk.common.logging.middleware.logger")
    def test_handle_exception_404(self, logger, report_exception):
        request = MagicMock()
        exception = DetailedException(None, "Test", 404)
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(request)

        rsp, status_code = middleware.handle_exception(exception)
        report_exception.assert_not_called()
        logger.log.assert_called_once()
        self.assertDictEqual({"code": None, "message": "Test"}, rsp)

    def test_get_logger_severity_info_error_code(self):
        test_code = 1242323
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        middleware.ignore_error_code(test_code)
        self.assertEqual(
            logging.INFO,
            middleware._get_logger_severity(400, test_code),
        )

    def test_get_logger_severity_info_status_code(self):
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        self.assertEqual(logging.INFO, middleware._get_logger_severity(412))
        self.assertEqual(logging.INFO, middleware._get_logger_severity(428))
        self.assertEqual(logging.INFO, middleware._get_logger_severity(429))

    def test_get_logger_severity_warn_status_code(self):
        status_code = 411
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        middleware.warn_error_code(status_code)
        self.assertEqual(
            logging.WARN,
            middleware._get_logger_severity(status_code),
        )

    def test_get_logger_severity_400(self):
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        self.assertEqual(logging.ERROR, middleware._get_logger_severity(400))
        self.assertEqual(logging.ERROR, middleware._get_logger_severity(401))
        self.assertEqual(logging.ERROR, middleware._get_logger_severity(402))
        self.assertEqual(logging.ERROR, middleware._get_logger_severity(403))

    def test_get_logger_severity_404(self):
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        self.assertEqual(logging.INFO, middleware._get_logger_severity(404))

    def test_get_logger_severity_405(self):
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        self.assertEqual(logging.INFO, middleware._get_logger_severity(405))

    def test_get_logger_severity_data_validation_error(self):
        with test_app.app_context():
            error_code = ErrorCodes.DATA_VALIDATION_ERROR

            test_cases = [
                ("GET", logging.ERROR),
                ("POST", logging.WARNING),
                ("PUT", logging.WARNING),
                ("PATCH", logging.WARNING),
            ]

            for method, expected in test_cases:
                middleware = RequestErrorHandlerMiddleware(
                    Request.from_values(method=method)
                )
                actual = middleware._get_logger_severity(400, error_code)
                self.assertEqual(
                    expected,
                    actual,
                    f"{logging.getLevelName(expected)} != {logging.getLevelName(actual)}",
                )

    def test_get_logger_severity_default(self):
        with test_app.app_context():
            middleware = RequestErrorHandlerMiddleware(Request({}))
        self.assertIsNone(middleware._get_logger_severity(200))

    def test_get_error_code(self):
        test_cases = [
            # body, expected error code
            ([], None),
            ({}, None),
            ({"code": 12345}, 12345),
        ]
        get_code = RequestErrorHandlerMiddleware._get_error_code
        for body, expected_code in test_cases:
            self.assertEqual(expected_code, get_code(body))
