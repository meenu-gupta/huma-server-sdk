"""consent model"""
from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.deployment.models.consent.consent_review import ConsentReview
from extensions.deployment.models.consent.consent_section import ConsentSection
from extensions.deployment.models.consent.consent_signature import ConsentSignature
from extensions.deployment.models.status import EnableStatus
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from extensions.deployment.models.localizable import Localizable
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
    validate_len,
    validate_entity_name,
)


class AnswerFormat(Enum):
    BOOLEAN = "BOOLEAN"
    TEXTCHOICE = "TEXTCHOICE"


@convertibleclass
class AdditionalConsentQuestion(Localizable):
    TYPE = "type"
    ENABLED = "enabled"
    FORMAT = "format"
    TEXT = "text"
    ORDER = "order"
    DESCRIPTION = "description"

    type: str = required_field()
    enabled: EnableStatus = required_field()
    format: AnswerFormat = required_field()
    text: str = required_field()
    description: str = default_field()
    order: int = field(default=0)

    _localizableFields: tuple[str, ...] = (TEXT, DESCRIPTION)


@convertibleclass
class Consent(Localizable):
    ID = "id"
    CREATE_DATE_TIME = "createDateTime"
    ENABLED = "enabled"
    REVIEW = "review"
    REVISION = "revision"
    SIGNATURE = "signature"
    SECTIONS = "sections"

    INSTITUTE_NAME = "instituteName"
    INSTITUTE_FULL_NAME = "instituteFullName"
    INSTITUTE_TEXT_DETAILS = "instituteTextDetails"
    ADDITIONAL_CONSENT_QUESTIONS = "additionalConsentQuestions"

    FIRST_VERSION = 1

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    enabled: EnableStatus = required_field()
    review: ConsentReview = default_field()
    revision: int = field(default=FIRST_VERSION)
    additionalConsentQuestions: list[AdditionalConsentQuestion] = default_field()
    signature: ConsentSignature = default_field()
    sections: list[ConsentSection] = default_field()
    instituteName: str = default_field(metadata=meta(validate_entity_name))
    instituteFullName: str = default_field(metadata=meta(validate_entity_name))
    instituteTextDetails: str = default_field(metadata=meta(validate_len(1, 30 * 1024)))

    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    def bump_revision(self, revision: int = None):
        self.revision = revision + 1 if revision else self.FIRST_VERSION

    _localizableFields: tuple[str, ...] = (
        SIGNATURE,
        ADDITIONAL_CONSENT_QUESTIONS,
        SECTIONS,
        REVIEW,
    )

    def has_agreement_section(self) -> bool:
        for section in self.sections:
            if section.type == ConsentSection.ConsentSectionType.AGREEMENT:
                return True
        return False
