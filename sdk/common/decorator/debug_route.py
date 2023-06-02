from functools import wraps

from sdk.common.exceptions.exceptions import PageNotFoundException
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig


def debug_route(except_obj: Exception = None):
    """
    Return a decorator which raises an exception when debugRouter value is False.
    """

    def main_decorator(func):
        @wraps(func)
        @autoparams("config")
        def wrapper(config: PhoenixServerConfig, *args, **kwargs):

            if not config.server.debugRouter:
                if except_obj:
                    raise except_obj
                raise PageNotFoundException

            return func(*args, **kwargs)

        return wrapper

    return main_decorator
