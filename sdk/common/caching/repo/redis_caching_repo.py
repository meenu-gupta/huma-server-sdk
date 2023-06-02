import json
from typing import Union

from redis import Redis

from sdk.common.caching.models import CachedObject
from sdk.common.caching.repo.caching_repo import CachingRepository
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.inject import autoparams


class RedisCachingRepository(CachingRepository):
    @autoparams()
    def __init__(self, redis: Redis):
        self._redis = redis

    def get(self, key: str) -> Union[CachedObject, None]:
        result = self._redis.get(key)
        if result:
            try:
                obj = CachedObject.from_dict(json.loads(result))
            except ConvertibleClassValidationError:
                return
            return obj

    def set(self, cached_object: CachedObject, expires_in: int):
        data = cached_object.to_dict(include_none=False)
        self._redis.set(cached_object.key, json.dumps(data), ex=expires_in)
