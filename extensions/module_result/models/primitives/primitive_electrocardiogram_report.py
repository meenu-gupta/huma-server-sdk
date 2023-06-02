"""Model for ElectrocardiogramReport object"""
from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive


@convertibleclass
class ElectrocardiogramReport(Primitive):
    """ElectrocardiogramReport model"""

    s3Object: S3Object = default_field(metadata=meta(S3Object, True))
