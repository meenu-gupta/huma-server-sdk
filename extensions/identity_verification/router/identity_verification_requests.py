from dataclasses import field
from datetime import datetime
from typing import Any

from extensions.identity_verification.models.identity_verification_log import (
    VerificationLog,
)
from sdk.common.exceptions.exceptions import BundleIdMissingException
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
    must_be_present,
    default_datetime_meta,
    must_not_be_present,
    validate_entity_name,
)


@convertibleclass
class GenerateIdentityVerificationTokenRequestObject:
    USER_ID = "userId"
    APPLICATION_ID = "applicationId"
    LEGAL_FIRST_NAME = "legalFirstName"
    LEGAL_LAST_NAME = "legalLastName"

    userId: str = required_field(
        metadata=meta(validate_object_id, value_to_field=str),
    )
    applicationId: str = default_field()
    legalFirstName: str = default_field(metadata=meta(validate_entity_name))
    legalLastName: str = default_field(metadata=meta(validate_entity_name))

    @classmethod
    def validate(cls, request_obj):
        if not request_obj.applicationId:
            raise BundleIdMissingException()


@convertibleclass
class CreateVerificationLogRequestObject(VerificationLog):
    @classmethod
    def validate(cls, request_obj):
        must_be_present(
            userId=request_obj.userId,
            applicantId=request_obj.applicantId,
        )
        must_not_be_present(verificationResult=request_obj.verificationResult)


@convertibleclass
class OnfidoVerificationResult:
    APPLICANT_ID = "applicant_id"
    STATUS = "status"
    RESULT = "result"

    id: str = default_field()
    created_at: datetime = default_field(metadata=default_datetime_meta())
    status: str = required_field(metadata=meta(VerificationLog.StatusType))
    result: str = required_field(metadata=meta(VerificationLog.ResultType))
    sandbox: bool = field(default=True)
    tags: list[Any] = default_field()
    results_uri: str = default_field()
    form_uri: str = default_field()
    paused: bool = field(default=False)
    version: str = default_field()
    report_ids: list[str] = default_field()
    href: str = default_field()
    applicant_id: str = required_field()
    applicant_provides_data: bool = field(default=False)


@convertibleclass
class OnfidoCallbackPayloadObject:
    id: str = default_field()
    status: str = default_field()
    completed_at_iso8601: datetime = default_field(metadata=default_datetime_meta())
    href: str = default_field()


@convertibleclass
class OnfidoCallbackPayload:
    resource_type: str = default_field()
    action: str = default_field()
    object: OnfidoCallbackPayloadObject = default_field()


@convertibleclass
class OnfidoCallBackVerificationRequestObject:
    PAYLOAD = "payload"

    payload: OnfidoCallbackPayload = default_field()
