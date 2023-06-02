from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import OxygenSaturation


class OxygenSaturationTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 0.81
        primitive = OxygenSaturation.create_from_dict(
            COMMON_FIELDS, name="OxygenSaturation"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "%")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 0.59
        self._assert_convertible_validation_err(OxygenSaturation)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 1.1
        self._assert_convertible_validation_err(OxygenSaturation)
