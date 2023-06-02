from sdk import convertibleclass
from sdk.common.utils.convertible import default_field
from sdk.common.utils.validators import default_version_meta
from sdk.versioning.models.version_field import VersionField


@convertibleclass
class IncreaseVersionRequestObject:
    SERVER_VERSION = "serverVersion"
    API_VERSION = "apiVersion"

    serverVersion: VersionField = default_field(metadata=default_version_meta())
    apiVersion: str = default_field()
