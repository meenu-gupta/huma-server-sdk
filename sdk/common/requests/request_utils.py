from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RequestContext:

    X_HU_LOCALE = "x-hu-locale"
    X_REQUEST_ID_HEADER_KEY = "X-Request-ID"

    def __getattr__(self, name):
        super().__getattribute__(name)

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __delattr__(self, name):
        super().__delattr__(name)

    def __contains__(self, name):
        return name in self.__dict__

    def get(self, name) -> Optional[Any]:
        if self.__contains__(name):
            return self.__dict__[name]
        else:
            return None
