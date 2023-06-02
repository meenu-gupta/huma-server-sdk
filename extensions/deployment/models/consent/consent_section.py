from dataclasses import field
from enum import Enum

from extensions.deployment.models.localizable import Localizable
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_entity_name, validate_len


@convertibleclass
class ConsentSectionOptions(Localizable):
    """Consent section model class"""

    TEXT = "text"

    type: int = required_field()
    text: str = required_field()
    order: int = field(default=0)
    abortOnChoose: bool = default_field()

    _localizableFields: tuple[str, ...] = (TEXT,)


@convertibleclass
class ConsentSection(Localizable):
    """Consent section model class"""

    class ConsentSectionType(Enum):
        OVERVIEW = "OVERVIEW"
        DATA_GATHERING = "DATA_GATHERING"
        PRIVACY = "PRIVACY"
        DATA_USE = "DATA_USE"
        TIME_COMMITMENT = "TIME_COMMITMENT"
        STUDY_SURVEY = "STUDY_SURVEY"
        STUDY_TASKS = "STUDY_TASKS"
        WITHDRAWING = "WITHDRAWING"
        SHARING = "SHARING"
        DATA_PROCESSING = "DATA_PROCESSING"
        FEEDBACK = "FEEDBACK"
        AGREEMENT = "AGREEMENT"

    SECTION_TYPE = "type"
    TITLE = "title"
    DETAILS = "details"
    REVIEW_DETAILS = "reviewDetails"
    OPTIONS = "options"
    TYPE = "type"

    type: ConsentSectionType = required_field()
    title: str = default_field(metadata=meta(validate_entity_name))
    details: str = default_field(metadata=meta(validate_len(1, 20 * 1024)))
    reviewDetails: str = default_field(metadata=meta(validate_len(1, 20 * 1024)))
    options: list[ConsentSectionOptions] = default_field()

    _localizableFields: tuple[str, ...] = (TITLE, DETAILS, REVIEW_DETAILS, OPTIONS)
