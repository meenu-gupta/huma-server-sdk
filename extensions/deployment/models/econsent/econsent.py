"""econsent model"""

from sdk.common.utils.convertible import convertibleclass, meta, required_field
from sdk.common.utils.validators import (
    validate_entity_name,
)
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.econsent.econsent_section import EConsentSection


@convertibleclass
class EConsent(Consent):
    TITLE = "title"
    OVERVIEW_TEXT = "overviewText"
    CONTACT_TEXT = "contactText"

    title: str = required_field(metadata=meta(validate_entity_name))
    overviewText: str = required_field()
    contactText: str = required_field()
    sections: list[EConsentSection] = required_field()

    _localizableFields: tuple[str, ...] = (
        Consent.SIGNATURE,
        Consent.ADDITIONAL_CONSENT_QUESTIONS,
        Consent.SECTIONS,
        TITLE,
        OVERVIEW_TEXT,
        CONTACT_TEXT,
        Consent.REVIEW,
    )
