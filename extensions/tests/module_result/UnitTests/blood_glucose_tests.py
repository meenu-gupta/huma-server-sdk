from extensions.module_result.models.primitives import BloodGlucose
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class BloodGlucoseTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 15
        primitive = BloodGlucose.create_from_dict(COMMON_FIELDS, name="BloodGlucose")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "mmol/L")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 0
        self._assert_convertible_validation_err(BloodGlucose)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 27
        self._assert_convertible_validation_err(BloodGlucose)
