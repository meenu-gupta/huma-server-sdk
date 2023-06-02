import abc
from typing import Union

from sdk.common.caching.models import CachedObject


class CachingRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str) -> Union[CachedObject, None]:
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, cached_object: CachedObject, expires_in: int):
        raise NotImplementedError
