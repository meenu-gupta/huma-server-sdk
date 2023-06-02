from extensions.module_result.models.primitives import (
    BodyMeasurement,
)
from extensions.module_result.modules import BVIModule
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_body_measurement,
)
from extensions.tests.module_result.UnitTests.primitives_tests import (
    COMMON_FIELDS,
    PrimitiveTestCase,
)


class BodyMeasurementTestCase(PrimitiveTestCase):
    def test_preferred_units_enabled(self):
        manager = ModulesManager()
        self.assertIn(
            BVIModule.moduleId, manager.get_preferred_unit_enabled_module_ids()
        )

    def test_success_creation(self):
        COMMON_FIELDS.update(sample_body_measurement())
        primitive = BodyMeasurement.create_from_dict(
            COMMON_FIELDS, name="BodyMeasurement"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.waistCircumferenceUnit, "cm")
        self.assertEqual(primitive.hipCircumferenceUnit, "cm")

    def test_failure_invalid_waist_circumference_value(self):
        invalid_values = [-5, 503]
        for value in invalid_values:
            COMMON_FIELDS[BodyMeasurement.WAIST_CIRCUMFERENCE] = value
            self._assert_convertible_validation_err(BodyMeasurement)

    def test_failure_invalid_hip_circumference_value(self):
        invalid_values = [-5, 503]
        for value in invalid_values:
            COMMON_FIELDS[BodyMeasurement.HIP_CIRCUMFERENCE] = value
            self._assert_convertible_validation_err(BodyMeasurement)
