import logging
import traceback
import uuid

from flask import Request, Response, g

from sdk.common.exceptions.exceptions import ErrorCodes, DetailedException
from sdk.common.monitoring.monitoring import report_exception
from sdk.common.utils.flask_request_utils import dump_request, dump_response
from sdk.phoenix.middlewares import Middleware

logger = logging.getLogger(__name__)


class RequestErrorHandlerMiddleware(Middleware):
    X_REQUEST_ID_HEADER_KEY = "X-Request-ID"

    INFO_ERROR_CODES = {
        ErrorCodes.DUPLICATED_USER_ID,
        ErrorCodes.INVALID_EMAIL_CONFIRMATION_CODE,
        ErrorCodes.INVALID_PASSWORD,
        ErrorCodes.INVALID_VERIFICATION_CODE,
        ErrorCodes.INVITATION_CODE_EXPIRED,
        ErrorCodes.INVALID_USERNAME_OR_PASSWORD,
        ErrorCodes.PASSWORD_EXPIRED,
        ErrorCodes.SESSION_TIMEOUT,
        ErrorCodes.SESSION_DOES_NOT_EXIST,
        ErrorCodes.TOKEN_EXPIRED,
        ErrorCodes.UPDATE_REQUIRED,
        ErrorCodes.UNAUTHORIZED,
        ErrorCodes.ALREADY_USED_PASSWORD,
    }
    WARN_ERROR_CODES = set()

    INFO_STATUS_CODES = {412, 428, 429}

    def __init__(self, request: Request):
        super(RequestErrorHandlerMiddleware, self).__init__(request)
        request_id = request.headers.get(self.X_REQUEST_ID_HEADER_KEY, None)
        self.request_id = g.uuid = g.get("uuid") or request_id or uuid.uuid4().hex

    @classmethod
    def ignore_error_code(cls, code: int):
        cls.INFO_ERROR_CODES.add(code)

    @classmethod
    def warn_error_code(cls, code: int):
        cls.WARN_ERROR_CODES.add(code)

    def before_request(self, request: Request):
        req_data = dump_request(self.request_id, request)
        logger.debug(req_data)

    def after_request(self, response: Response):
        response.direct_passthrough = False
        response.headers[self.X_REQUEST_ID_HEADER_KEY] = self.request_id
        error_code = self._get_error_code(response.json)
        severity = self._get_logger_severity(response.status_code, error_code)
        severity = logging.WARNING if severity == logging.ERROR else severity
        if severity:
            req_data = dump_request(self.request_id, self.request)
            resp_data = dump_response(self.request_id, response)
            for data in [req_data, resp_data]:
                logger.log(severity, data)

    def handle_exception(self, e: DetailedException) -> tuple[dict, int]:
        severity = self._get_logger_severity(e.status_code, e.code)
        error_dict = e.to_dict()
        if not severity:
            return error_dict, e.status_code

        if severity >= logging.ERROR:
            if not self.skip_error_log():
                report_exception(e)
        else:
            msg = f"""errorhandler with details: {str(error_dict)}\nMore details: {traceback.format_exc()}"""
            logger.log(severity, msg)

        return error_dict, e.status_code

    @staticmethod
    def skip_error_log():
        try:
            return g.get("is_automation_request", False)
        except RuntimeError:
            return False

    def _get_logger_severity(self, status_code: int, error_code: int = None) -> int:
        if status_code in self.WARN_ERROR_CODES:
            return logging.WARN

        elif status_code in self.INFO_STATUS_CODES:
            return logging.INFO

        elif error_code in self.INFO_ERROR_CODES:
            return logging.INFO

        elif status_code in (404, 405) and error_code is None:
            return logging.INFO

        elif (
            self.request.method in ("POST", "PUT", "PATCH")
            and error_code == ErrorCodes.DATA_VALIDATION_ERROR
        ):
            return logging.WARNING

        elif status_code >= 400:
            return logging.ERROR

    @staticmethod
    def _get_error_code(body) -> int:
        if body and isinstance(body, dict):
            return body.get("code")
