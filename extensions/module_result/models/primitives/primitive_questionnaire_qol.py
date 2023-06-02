from extensions.module_result.common.enums import Regularly
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class AdditionalQoL(SkippedFieldsMixin, Primitive):
    """AdditionalQoL model"""

    VIEW_FAMILY = "viewFamily"
    CONTACT_PROFESSIONALS = "contactProfessionals"
    CONTRIBUTE_ACTIVITIES = "contributeActivities"
    METADATA = "metadata"

    viewFamily: Regularly = required_field()
    contactProfessionals: Regularly = required_field()
    contributeActivities: Regularly = required_field()
    metadata: QuestionnaireMetadata = required_field()
