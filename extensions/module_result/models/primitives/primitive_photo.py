"""model for photo object"""
from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class Photo(Primitive):
    """Photo model"""

    s3Object: S3Object = required_field()
    s3Thumbnail: S3Object = default_field()
    width: float = default_field(metadata=meta(value_to_field=float))
    height: float = default_field(metadata=meta(value_to_field=float))
    note: str = default_field()
