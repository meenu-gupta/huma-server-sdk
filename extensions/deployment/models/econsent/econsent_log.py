from datetime import datetime
from enum import IntEnum

from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.common_functions_utils import get_full_name_for_signature
from sdk.common.utils.validators import (
    default_datetime_meta,
    validate_object_id,
    str_id_to_obj_id,
)

from extensions.common.s3object import S3Object
from extensions.deployment.models.consent.consent_log import ConsentLog


@convertibleclass
class EConsentLog(ConsentLog):
    """EConsent Log model."""

    _ID = "_id"

    ECONSENT_ID = "econsentId"
    PDF_LOCATION = "pdfLocation"
    CONSENT_OPTION = "consentOption"
    END_DATE_TIME = "endDateTime"

    class EConsentOption(IntEnum):
        NOT_PARTICIPATE = 0
        UNDERSTAND_AND_ACCEPT = 1

    econsentId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    pdfLocation: S3Object = default_field()
    consentOption: EConsentOption = default_field()
    endDateTime: datetime = default_field(metadata=default_datetime_meta())

    def get_full_name(self):
        return get_full_name_for_signature(
            given_name=self.givenName, family_name=self.familyName
        ).upper()
