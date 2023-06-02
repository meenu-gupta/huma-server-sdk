from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class ECGAliveCor(Primitive):
    """ECGAliveCor model."""

    S3_OBJECT = "s3Object"
    KARDIA_ECG_RECORD_ID = "kardiaEcgRecordId"

    s3Object: S3Object = required_field()
    kardiaEcgRecordId: str = required_field()
