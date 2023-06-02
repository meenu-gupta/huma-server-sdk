from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import (
    Temperature,
)


class TemperatureTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 36.6
        primitive = Temperature.create_from_dict(COMMON_FIELDS, name="Temperature")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "oC")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 32
        self._assert_convertible_validation_err(Temperature)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 43
        self._assert_convertible_validation_err(Temperature)
