from dataclasses import field
from datetime import datetime
from typing import Any

from extensions.medication.models.medication import Medication
from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from sdk.common.utils.validators import (
    must_not_be_present,
    must_be_present,
    default_datetime_meta,
)


class CreateMedicationRequestObject(Medication):
    @classmethod
    def validate(cls, medication):
        must_be_present(name=medication.name)
        must_not_be_present(
            id=medication.id,
            createDateTime=medication.createDateTime,
            updateDateTime=medication.updateDateTime,
            changeHistory=medication.changeHistory,
        )


class UpdateMedicationRequestObject(Medication):
    @classmethod
    def validate(cls, medication):
        must_be_present(id=medication.id)
        must_not_be_present(changeHistory=medication.changeHistory)


@convertibleclass
class RetrieveMedicationsRequestObject:
    USER_ID = "userId"
    SKIP = "skip"
    LIMIT = "limit"

    userId: str = required_field()
    skip: int = required_field()
    limit: int = required_field()
    startDateTime: datetime = default_field(metadata=default_datetime_meta())
    onlyEnabled: bool = field(default=True)


@convertibleclass
class DeleteMedicationRequestObject:
    USER_ID = "userId"
    SESSION = "session"

    userId: str = required_field()
    session: Any = default_field()
