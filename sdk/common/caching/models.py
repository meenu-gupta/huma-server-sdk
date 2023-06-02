from dataclasses import field
from typing import Any

from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import default_version_meta
from sdk.versioning.models.version_field import VersionField


@convertibleclass
class CachedObject:
    KEY = "key"
    VERSION = "version"
    CONTENT = "content"
    CONTENT_HASH = "contentHash"

    key: str = required_field()
    version: VersionField = default_field(metadata=default_version_meta())
    content: Any = default_field()
    contentHash: str = default_field()
