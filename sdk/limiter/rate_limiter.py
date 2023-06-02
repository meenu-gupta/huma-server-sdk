from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr


class RateLimiter(Limiter):
    def __init__(self, app: Flask, default_limit: str = None, storage_uri: str = None):
        super(RateLimiter, self).__init__(
            app,
            key_func=get_ipaddr,
            default_limits=[default_limit],
            storage_uri=storage_uri,
        )
