from enum import IntEnum

from sdk import convertibleclass
from sdk.common.utils.convertible import required_field
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


class CurrentGroupCategory(IntEnum):
    PREGNANT = 0
    NOT_PREGNANT = 1


@convertibleclass
class AZFurtherPregnancyKeyActionTrigger(SkippedFieldsMixin, Primitive):
    CURRENT_GROUP_CATEGORY = "currentGroupCategory"
    METADATA = "metadata"

    currentGroupCategory: CurrentGroupCategory = required_field()
    metadata: QuestionnaireMetadata = required_field()
