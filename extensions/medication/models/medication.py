"""model for Medication"""
from datetime import datetime
from enum import Enum

from extensions.medication.models.medication_schedule import MedicationSchedule
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
    str_id_to_obj_id,
    default_datetime_meta,
    validate_len,
)


def history_to_dict(data):
    ignored_fields = [Medication.USER_ID, Medication.DEPLOYMENT_ID]
    return [i.to_dict(include_none=False, ignored_fields=ignored_fields) for i in data]


@convertibleclass
class MedicationBase:
    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    prn: bool = default_field()
    enabled: bool = default_field()
    userId: str = required_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    deploymentId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    moduleId: str = default_field()
    name: str = default_field(metadata=meta(validate_len(1, 45)))
    doseQuantity: float = default_field(
        metadata=meta(lambda f: f >= 0.0, value_to_field=float)
    )
    doseUnits: str = default_field(metadata=meta(validate_len(1, 40)))
    schedule: MedicationSchedule = default_field()
    extraProperties: dict = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    ID = "id"
    ID_ = "_id"
    PRN = "prn"
    NAME = "name"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    MODULE_ID = "moduleId"
    ENABLED = "enabled"
    SCHEDULE = "schedule"
    DOSE_UNITS = "doseUnits"
    DOSE_QUANTITY = "doseQuantity"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    EXTRA_PROPERTIES = (
        "extraProperties"
        # Dict containing {"note": str (the contents of the note)}
    )


@convertibleclass
class MedicationHistory(MedicationBase):
    CHANGE_TYPE = "changeType"

    class ChangeType(Enum):
        MEDICATION_UPDATE = "MEDICATION_UPDATE"
        MEDICATION_CREATE = "MEDICATION_CREATE"
        MEDICATION_DELETE = "MEDICATION_DELETE"

    changeType: ChangeType = default_field()


@convertibleclass
class Medication(MedicationBase):
    """A Medication is a single compound that can be taken by a user. It can be scheduled."""

    changeHistory: list[MedicationHistory] = default_field(
        metadata=meta(field_to_value=history_to_dict),
    )

    CHANGE_HISTORY = "changeHistory"  # List of dicts containing changes


class Action(Enum):
    CreateMedication = "CreateMedication"
    UpdateMedication = "UpdateMedication"
