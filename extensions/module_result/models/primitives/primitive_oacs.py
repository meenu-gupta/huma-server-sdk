from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
)
from .primitive import Primitive


@convertibleclass
class OACS(Primitive):

    OACS_SCORE = "oacsScore"

    oacsScore: float = required_field(metadata=meta(value_to_field=float))

    _scoring_answers = None

    @property
    def scoring_answers(self):
        return self._scoring_answers

    @scoring_answers.setter
    def scoring_answers(self, value):
        self._scoring_answers = value
