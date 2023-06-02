from typing import Any, Union

from sdk.common.caching.models import CachedObject
from sdk.common.caching.repo.caching_repo import CachingRepository
from sdk.common.constants import DAY
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.versioning.models.version import Version


class CachingService:
    @autoparams()
    def __init__(self, repo: CachingRepository, version: Version):
        self.repo = repo
        self.version = version

    def get(self, key: str) -> Union[CachedObject, None]:
        obj = self.repo.get(key)
        if obj and obj.version == self.version.server:
            return obj

    def set(
        self, key: str, content: Any, content_hash: str, expires_in=DAY
    ):  # exp in 24h
        data = {
            CachedObject.KEY: key,
            CachedObject.VERSION: self.version.server,
            CachedObject.CONTENT: content,
            CachedObject.CONTENT_HASH: content_hash,
        }
        cached_object = CachedObject.from_dict(remove_none_values(data))
        self.repo.set(cached_object, expires_in)
