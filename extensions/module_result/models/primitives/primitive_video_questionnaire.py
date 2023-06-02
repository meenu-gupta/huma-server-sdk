"""
    Model for VideoQuestionnaire
"""
from extensions.common.s3object import S3Object
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_id
from .primitive import Primitive


@convertibleclass
class VideoQuestionnaireStep:
    """VideoQuestionnaire::VideoQuestionnaireStep model"""

    S3OBJECT = "s3Object"
    START_DATE_TIME = "startDateTime"

    id: str = default_field(metadata=meta(validate_id))
    # S3Object representing the answer of the client
    s3Object: S3Object = required_field()
    s3thumbnail: S3Object = default_field()
    # Should be ignored if VideoQuestionnaireConfig::Step[stepId].note.enabled == False
    note: str = default_field()
    startDateTime: int = required_field()


@convertibleclass
class VideoQuestionnaire(Primitive):
    """VideoQuestionnaire model"""

    STEPS = "steps"

    steps: list[VideoQuestionnaireStep] = required_field()
