import unittest

from extensions.module_result.models.primitives.primitive_oxford_knee import (
    OxfordKneeScore,
    LegData,
)
from extensions.module_result.models.primitives import Primitive
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_oxford_both_knee_score,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "60fa9d91632c017458608307"


def oxford_knee_score_sample():
    return {
        **sample_oxford_both_knee_score(),
        Primitive.USER_ID: SAMPLE_ID,
        Primitive.MODULE_ID: SAMPLE_ID,
    }


class OxfordKneeScoreTestCase(unittest.TestCase):
    def test_success_oks_primitive_creation(self):
        data = oxford_knee_score_sample()
        try:
            OxfordKneeScore.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_fields(self):
        non_answers_fields = [LegData.LEG_AFFECTED, LegData.SCORE]
        required_fields = [
            i for i in LegData().__annotations__.keys() if i not in non_answers_fields
        ]
        for key in required_fields:
            data = oxford_knee_score_sample()
            data[OxfordKneeScore.LEGS_DATA][0].pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                OxfordKneeScore.from_dict(data)

        required_fields = [OxfordKneeScore.LEGS_DATA, OxfordKneeScore.LEG_AFFECTED]
        for key in required_fields:
            data = oxford_knee_score_sample()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                OxfordKneeScore.from_dict(data)


if __name__ == "__main__":
    unittest.main()
