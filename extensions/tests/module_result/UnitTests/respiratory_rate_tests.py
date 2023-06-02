from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)

from extensions.module_result.models.primitives import RespiratoryRate


class RespiratoryRateTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 30
        primitive = RespiratoryRate.create_from_dict(
            COMMON_FIELDS, name="RespiratoryRate"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "rpm")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 5
        self._assert_convertible_validation_err(RespiratoryRate)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 31
        self._assert_convertible_validation_err(RespiratoryRate)
