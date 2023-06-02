from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import Weight


class WeightTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 55
        primitive = Weight.create_from_dict(COMMON_FIELDS, name="Weight")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "kg")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 19
        self._assert_convertible_validation_err(Weight)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 301
        self._assert_convertible_validation_err(Weight)
