from abc import abstractmethod, ABC
from typing import Any

from flask import Request, Response

from sdk.common.exceptions.exceptions import DetailedException


class Middleware(ABC):
    def __init__(self, request: Request):
        self.request = request

    @abstractmethod
    def after_request(self, response: Response):
        raise NotImplementedError

    @abstractmethod
    def before_request(self, request: Request):
        raise NotImplementedError

    @abstractmethod
    def handle_exception(self, exception: DetailedException) -> tuple[Any, int]:
        raise NotImplementedError
