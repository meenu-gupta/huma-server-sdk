from extensions.deployment.models.localizable import Localizable
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field


@convertibleclass
class ConsentReview(Localizable):
    """Consent review model class"""

    TITLE = "title"
    DETAILS = "details"

    title: str = required_field()
    details: str = required_field()

    _localizableFields: tuple[str, ...] = (TITLE, DETAILS)
