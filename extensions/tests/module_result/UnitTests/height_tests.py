from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import Height


class HeightTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 160
        primitive = Height.create_from_dict(COMMON_FIELDS, name="Height")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "cm")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 99
        self._assert_convertible_validation_err(Height)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 251
        self._assert_convertible_validation_err(Height)
