from extensions.module_result.module_result_utils import (
    PoorToExcellent,
    NotToCompletely,
    AlwaysToNever,
    VerySevereToNone,
)
from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    meta,
    default_field,
)
from sdk.common.utils.validators import validate_range
from .primitive import Primitive, SkippedFieldsMixin
from .primitive_questionnaire import QuestionnaireAppResult, QuestionnaireMetadata


@convertibleclass
class PROMISGlobalHealth(SkippedFieldsMixin, Primitive):
    GLOBAL_01 = "global01"
    GLOBAL_02 = "global02"
    GLOBAL_03 = "global03"
    GLOBAL_04 = "global04"
    GLOBAL_05 = "global05"
    GLOBAL_06 = "global06"
    GLOBAL_07_RC = "global07rc"
    GLOBAL_08_R = "global08r"
    GLOBAL_09_R = "global09r"
    GLOBAL_10_R = "global10r"
    METADATA = "metadata"

    global01: PoorToExcellent = required_field()
    global02: PoorToExcellent = required_field()
    global03: PoorToExcellent = required_field()
    global04: PoorToExcellent = required_field()
    global05: PoorToExcellent = required_field()
    global06: NotToCompletely = required_field()
    global07rc: int = required_field(
        metadata=meta(validate_range(0, 10), value_to_field=int)
    )
    global08r: VerySevereToNone = required_field()

    global09r: PoorToExcellent = required_field()
    global10r: AlwaysToNever = required_field()
    mentalHealthValue: float = default_field(metadata=meta(value_to_field=float))
    mentalHealthResult: QuestionnaireAppResult = default_field()
    physicalHealthValue: float = default_field()
    physicalHealthResult: QuestionnaireAppResult = default_field()
    metadata: QuestionnaireMetadata = required_field()
