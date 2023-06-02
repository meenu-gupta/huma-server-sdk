import unittest

from extensions.module_result.models.primitives.primitive_oxford_hip import HipData
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_oxford_hip import (
    OxfordHipScore,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_oxford_both_hip_score,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "60fa9d91632c017458608307"


def oxford_hip_score_sample():
    return {
        **sample_oxford_both_hip_score(),
        Primitive.USER_ID: SAMPLE_ID,
        Primitive.MODULE_ID: SAMPLE_ID,
    }


class OxfordHipScoreTestCase(unittest.TestCase):
    def test_success_ohs_primitive_creation(self):
        data = oxford_hip_score_sample()
        try:
            OxfordHipScore.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_fields(self):
        non_answers_fields = [HipData.HIP_AFFECTED, HipData.SCORE]
        required_fields = [
            i for i in HipData().__annotations__.keys() if i not in non_answers_fields
        ]
        for key in required_fields:
            data = oxford_hip_score_sample()
            data[OxfordHipScore.HIPS_DATA][0].pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                OxfordHipScore.from_dict(data)

        required_fields = [OxfordHipScore.HIPS_DATA, OxfordHipScore.HIP_AFFECTED]
        for key in required_fields:
            data = oxford_hip_score_sample()
            data.pop(key)
            with self.assertRaises(ConvertibleClassValidationError):
                OxfordHipScore.from_dict(data)


if __name__ == "__main__":
    unittest.main()
