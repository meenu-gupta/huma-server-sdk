from enum import Enum
from dataclasses import field
from datetime import datetime

from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
    str_id_to_obj_id,
)


@convertibleclass
class Document:
    ID = "id"
    IS_ACTIVE = "isActive"

    id: str = default_field()
    isActive: bool = default_field()

    @staticmethod
    def value_to_field(id_: str):
        if isinstance(id_, str):
            return {Document.ID: id_, Document.IS_ACTIVE: True}
        return id_


@convertibleclass
class VerificationLog:
    """Verification Log model"""

    class StatusType(Enum):
        COMPLETE = "complete"
        WITHDRAWN = "withdrawn"
        PAUSED = "paused"
        AWAITING_DATA = "awaiting_data"
        AWAITING_APPROVAL = "awaiting_approval"

    class ResultType(Enum):
        CLEAR = "clear"
        CONSIDER = "consider"

    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    APPLICANT_ID = "applicantId"
    VERIFICATION_STATUS = "verificationStatus"
    VERIFICATION_RESULT = "verificationResult"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    CHECK_ID = "checkId"
    LEGAL_FIRST_NAME = "legalFirstName"
    LEGAL_LAST_NAME = "legalLastName"
    DOCUMENTS = "documents"

    _id_meta = meta(validate_object_id, False, str_id_to_obj_id, str)

    id: str = default_field(metadata=_id_meta)
    userId: str = default_field(metadata=_id_meta)
    deploymentId: str = default_field(metadata=_id_meta)
    applicantId: str = default_field()
    verificationStatus: StatusType = field(default=StatusType.AWAITING_APPROVAL)
    verificationResult: ResultType = default_field()
    checkId: str = default_field()
    legalFirstName: str = default_field()
    legalLastName: str = default_field()
    documents: list[Document] = default_field(
        metadata=meta(value_to_field=lambda x: list(map(Document.value_to_field, x))),
    )
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
