"""model for s3object"""
from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, required_field, default_field


@convertibleclass
class S3Object:
    """s3object"""

    BUCKET = "bucket"
    KEY = "key"
    REGION = "region"

    bucket: str = required_field()
    key: str = required_field()
    region: str = default_field()


@convertibleclass
class FlatBufferS3Object(S3Object):
    """Used to process separately flat buffer object"""

    FBS_VERSION = "fbsVersion"

    fbsVersion: int = field(default=0)
