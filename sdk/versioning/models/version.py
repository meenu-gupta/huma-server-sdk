from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import default_version_meta
from sdk.versioning.models.version_field import VersionField


@convertibleclass
class Version:
    API = "api"
    BUILD = "build"
    SERVER = "server"

    server: VersionField = required_field(metadata=default_version_meta())
    api: str = required_field()
    build: str = default_field()
