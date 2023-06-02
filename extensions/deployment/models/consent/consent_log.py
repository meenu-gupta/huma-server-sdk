from datetime import datetime

from extensions.common.s3object import S3Object
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
    validate_entity_name,
    validate_id,
)


@convertibleclass
class ConsentLog:
    """Consent Log model."""

    ID = "id"
    ID_ = "_id"
    USER_ID = "userId"
    CONSENT_ID = "consentId"
    REVISION = "revision"
    GIVEN_NAME = "givenName"
    MIDDLE_NAME = "middleName"
    FAMILY_NAME = "familyName"
    CREATE_DATE_TIME = "createDateTime"
    SIGNATURE = "signature"
    SHARING_OPTION = "sharingOption"
    AGREEMENT = "agreement"
    DEPLOYMENT_ID = "deploymentId"
    ADDITIONAL_CONSENT_ANSWERS = "additionalConsentAnswers"

    id: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    userId: str = required_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    consentId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    revision: int = default_field()
    givenName: str = default_field(metadata=meta(validate_entity_name))
    middleName: str = default_field(metadata=meta(validate_entity_name))
    familyName: str = default_field(metadata=meta(validate_entity_name))
    signature: S3Object = default_field()
    sharingOption: int = default_field()
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    agreement: bool = default_field()
    deploymentId: str = required_field(metadata=meta(validate_id))
    additionalConsentAnswers: dict = default_field()
