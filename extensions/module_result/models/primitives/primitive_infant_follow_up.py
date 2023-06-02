from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireMetadata


@convertibleclass
class ChildrenItem:
    ISSUES = "issues"
    ADDITIONAL_INFO = "additionalInfo"
    HAS_CHILD_DEVELOP_ISSUES = "hasChildDevelopIssues"

    issues: list[str] = default_field()
    additionalInfo: str = default_field()
    hasChildDevelopIssues: bool = required_field()


@convertibleclass
class InfantFollowUp(SkippedFieldsMixin, Primitive):
    """InfantFollowUp model"""

    CHILDREN = "children"
    METADATA = "metadata"
    IS_COV_PREG_LIVE_BIRTH = "isCovPregLiveBirth"
    IS_MORE_THAN_1_CHILD_COV_VAC = "isMoreThan1ChildCovVac"
    COUNT_COV_PREG = "countCovPreg"

    isCovPregLiveBirth: bool = required_field()
    isMoreThan1ChildCovVac: bool = default_field()
    countCovPreg: int = default_field()
    children: list[ChildrenItem] = default_field()
    metadata: QuestionnaireMetadata = required_field()
