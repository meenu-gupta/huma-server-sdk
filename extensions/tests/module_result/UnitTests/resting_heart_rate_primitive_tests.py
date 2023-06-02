import unittest

from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_resting_heartrate import (
    RestingHeartRate,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class RestingHeartRateTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            RestingHeartRate.VALUE: 3,
        }

    def test_success_create_resting_heart_rate_primitive(self):
        data = self._sample_data()
        try:
            RestingHeartRate.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_resting_heart_rate__no_required_field(self):
        data = self._sample_data()
        data.pop(RestingHeartRate.VALUE)
        with self.assertRaises(ConvertibleClassValidationError):
            RestingHeartRate.from_dict(data)


if __name__ == "__main__":
    unittest.main()
