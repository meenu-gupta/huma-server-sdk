from datetime import datetime
from enum import Enum

from extensions.common.s3object import S3Object
from extensions.module_result.models.primitives import Primitive
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_object_id,
    str_id_to_obj_id,
    default_datetime_meta,
)


@convertibleclass
class RevereTestResult(Primitive):
    INITIAL_WORDS = "initialWords"
    AUDIO_RESULT = "audioResult"
    WORDS_RESULT = "wordsResult"
    INPUT_LANGUAGE_IETF_TAG = "inputLanguageIETFTag"
    BUILD_NUMBER = "buildNumber"

    initialWords: list[str] = required_field()
    audioResult: S3Object = default_field()
    wordsResult: list[str] = default_field()
    inputLanguageIETFTag: str = default_field()
    buildNumber: str = default_field()


@convertibleclass
class RevereTest:
    class Status(Enum):
        STARTED = "STARTED"
        FINISHED = "FINISHED"

    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    RESULTS = "results"
    STATUS = "status"
    MODULE_ID = "moduleId"
    DEPLOYMENT_ID = "deploymentId"

    id: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    userId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    startDateTime: datetime = default_field(metadata=default_datetime_meta())
    endDateTime: datetime = default_field(metadata=default_datetime_meta())
    results: list[RevereTestResult] = default_field()
    status: Status = default_field()

    # needed for export compatibility
    moduleId: str = required_field()
    deploymentId: str = required_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )


class RevereAction(Enum):
    StartTest = "StartTest"
    UploadAudioResult = "UploadAudioResult"
    FinishTest = "FinishTest"
    ExportTestResult = "ExportTestResult"
    ExportRevere = "ExportRevere"
