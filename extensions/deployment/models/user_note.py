""" User Note model """
from datetime import datetime
from enum import Enum

from extensions.module_result.models.primitives import QuestionnaireAnswer
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
    validate_entity_name,
)


@convertibleclass
class UserNote:

    """UserNote Type Enum"""

    class UserNoteType(Enum):
        CAREPLANGROUPLOG = "CAREPLANGROUPLOG"
        OBSERVATION_NOTES = "OBSERVATION_NOTES"
        USER_OBSERVATION_NOTES = "USER_OBSERVATION_NOTES"

    ID_ = "_id"
    ID = "id"
    TYPE = "type"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    FROM_CARE_PLAN_GROUP_ID = "fromCarePlanGroupId"
    TO_CARE_PLAN_GROUP_ID = "toCarePlanGroupId"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"
    NOTE = "note"
    MODULE_CONFIG_ID = "moduleConfigId"
    ANSWERS = "answers"
    QUESTIONNAIRE_ID = "questionnaireId"
    CREATE_DATE_TIME = "createDateTime"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    type: UserNoteType = required_field()
    userId: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    deploymentId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    fromCarePlanGroupId: str = default_field(metadata=meta(validate_entity_name))
    toCarePlanGroupId: str = default_field(metadata=meta(validate_entity_name))
    submitterId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    submitterName: str = default_field(metadata=meta(validate_entity_name))
    note: str = default_field()
    moduleConfigId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    answers: list[QuestionnaireAnswer] = default_field()
    questionnaireId: str = default_field()
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
