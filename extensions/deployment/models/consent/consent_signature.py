from dataclasses import field

from extensions.deployment.models.localizable import Localizable
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field


@convertibleclass
class ConsentSignature(Localizable):
    """Consent signature model class"""

    SIGNATURE_TITLE = "signatureTitle"
    SIGNATURE_DETAILS = "signatureDetails"
    NAME_TITLE = "nameTitle"
    NAME_DETAILS = "nameDetails"

    signatureTitle: str = required_field()
    signatureDetails: str = required_field()
    nameTitle: str = required_field()
    nameDetails: str = required_field()
    hasMiddleName: bool = field(default=True)
    showFirstLastName: bool = field(default=True)

    _localizableFields: tuple[str, ...] = (
        SIGNATURE_TITLE,
        SIGNATURE_DETAILS,
        NAME_TITLE,
        NAME_DETAILS,
    )
