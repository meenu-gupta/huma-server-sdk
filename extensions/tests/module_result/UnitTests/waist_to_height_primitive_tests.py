import unittest

from extensions.module_result.models.primitives import WaistToHeight, Primitive
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class WaistToHeightPrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            WaistToHeight.HEIGHT: 176,
            WaistToHeight.WAIST: 60,
        }

    def test_failure_no_required_field(self):
        data = self._sample_data()
        data.pop(WaistToHeight.HEIGHT)
        with self.assertRaises(ConvertibleClassValidationError):
            WaistToHeight.from_dict(data)

    def test_success_creation(self):
        data = self._sample_data()
        primitive = WaistToHeight.from_dict(data)
        self.assertEqual(0.3409090909090909, primitive.value)

    def test_failure_validation_waist_is_bigger_than_height(self):
        data = self._sample_data()
        data[WaistToHeight.WAIST] = 7868567645
        with self.assertRaises(ConvertibleClassValidationError):
            WaistToHeight.from_dict(data)


if __name__ == "__main__":
    unittest.main()
