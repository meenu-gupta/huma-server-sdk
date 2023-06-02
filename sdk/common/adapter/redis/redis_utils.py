import hashlib
import json
from typing import Union

from redis import Redis


def cache_is_accessible(cache: Redis):
    try:
        cache.ping()
    except ConnectionError:
        return False

    return True


def calculate_hashed_value(data: Union[list, dict, str]):
    bytes_data = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.md5(bytes_data).hexdigest()
