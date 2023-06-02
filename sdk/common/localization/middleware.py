from flask import Request, Response, g
from typing import Any

from sdk.common.utils.validators import incorrect_language_to_default
from sdk.phoenix.middlewares import Middleware
from sdk.common.exceptions.exceptions import DetailedException


class LocalizationMiddleware(Middleware):
    X_HU_LOCALE = "x-hu-locale"

    def __init__(self, request: Request):
        super(LocalizationMiddleware, self).__init__(request)
        self.request = request

    def _get_language_from_header(self):
        new_language = self.request.headers.get(self.X_HU_LOCALE)
        if not new_language:
            return

        return incorrect_language_to_default(new_language)

    def before_request(self, request: Request):
        g.language = self._get_language_from_header()

    def after_request(self, response: Response):
        pass

    def handle_exception(self, exception: DetailedException) -> tuple[Any, int]:
        pass
