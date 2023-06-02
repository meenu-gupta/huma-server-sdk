from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import (
    BloodPressure,
)


class BloodPressureTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["diastolicValue"] = 80
        COMMON_FIELDS["systolicValue"] = 80
        primitive = BloodPressure.create_from_dict(COMMON_FIELDS, name="BloodPressure")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.diastolicValueUnit, "mmHg")
        self.assertEqual(primitive.systolicValueUnit, "mmHg")

    def test_failed_diastolic_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 29
        self._assert_convertible_validation_err(BloodPressure)

    def test_failed_diastolic_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 131
        self._assert_convertible_validation_err(BloodPressure)

    def test_failed_systolic_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 59
        self._assert_convertible_validation_err(BloodPressure)

    def test_failed_systolic_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 261
        self._assert_convertible_validation_err(BloodPressure)
