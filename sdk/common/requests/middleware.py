from typing import Any
from flask import Request
from flask.wrappers import Response
from sdk.common.exceptions.exceptions import DetailedException

from sdk.phoenix.middlewares import Middleware
from sdk.common.utils import inject
from .request_utils import RequestContext


class RequestContextMiddleware(Middleware):
    def _get_language(self):
        return self.request.headers.get(RequestContext.X_HU_LOCALE)

    def _get_request_id(self):
        return self.request.headers.get(RequestContext.X_REQUEST_ID_HEADER_KEY)

    def before_request(self, request: Request):

        request_obj = RequestContext()
        request_obj.locale = self._get_language()
        request_obj.request_id = self._get_request_id()

        inject.get_injector_or_die().rebind(
            lambda x: x.bind(RequestContext, request_obj)
        )

    def after_request(self, response: Response):
        pass

    def handle_exception(self, exception: DetailedException) -> tuple[Any, int]:
        pass
