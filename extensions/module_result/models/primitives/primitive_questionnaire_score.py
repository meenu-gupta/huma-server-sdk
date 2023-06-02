""" Model for Questionnaire Score Result objects """
from enum import Enum

from sdk.common.utils.convertible import convertibleclass, meta, default_field
from .primitive import Primitive
from .primitive_questionnaire import QuestionnaireAppResult


@convertibleclass
class QuestionnaireScore(Primitive):
    """Questionnaire Score model"""

    class QuestionnaireName(Enum):
        PAM_13 = 1

    appResult: QuestionnaireAppResult = default_field()
    error: str = default_field()
    questionnaireResultId: str = default_field()
    questionnaireName: QuestionnaireName = default_field()
    value: float = default_field(metadata=meta(value_to_field=float))
    # Full response payload from API endpoint
    fullResponse: str = default_field()
