from packaging.version import InvalidVersion, Version as PackagingVersion

from sdk import convertibleclass


@convertibleclass
class VersionField(PackagingVersion):
    def __init__(self, version: str) -> None:
        from sdk.common.utils.validators import is_valid_semantic_version

        if not is_valid_semantic_version(version):
            raise InvalidVersion(f"Invalid version: '{version}'")
        super().__init__(version)
