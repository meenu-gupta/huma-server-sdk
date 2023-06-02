import copy

from extensions.module_result.modules import PROMISGlobalHealthModule
from extensions.module_result.models.primitives import PROMISGlobalHealth
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class PROMISGlobalHealthTestCase(PrimitiveTestCase):
    def _assign_primitive_values(self):
        COMMON_FIELDS.update(
            {
                PROMISGlobalHealth.GLOBAL_01: 5,
                PROMISGlobalHealth.GLOBAL_02: 5,
                PROMISGlobalHealth.GLOBAL_03: 5,
                PROMISGlobalHealth.GLOBAL_04: 5,
                PROMISGlobalHealth.GLOBAL_05: 5,
                PROMISGlobalHealth.GLOBAL_06: 5,
                PROMISGlobalHealth.GLOBAL_07_RC: 0,
                PROMISGlobalHealth.GLOBAL_08_R: 5,
                PROMISGlobalHealth.GLOBAL_09_R: 5,
                PROMISGlobalHealth.GLOBAL_10_R: 5,
                "metadata": {"answers": []},
            }
        )

    def test_success_calculate_result_case_1(self):
        self._assign_primitive_values()
        primitive: PROMISGlobalHealth = PROMISGlobalHealth.from_dict(COMMON_FIELDS)
        module = PROMISGlobalHealthModule()
        module.calculate(primitive)

        global_7_rc = 5
        self.assertEqual(global_7_rc, primitive.global07rc)
        self.assertEqual(67.6, primitive.mentalHealthValue)
        self.assertEqual(67.7, primitive.physicalHealthValue)

    def test_success_calculate_result_case_2(self):
        COMMON_FIELDS.update(
            {
                PROMISGlobalHealth.GLOBAL_01: 1,
                PROMISGlobalHealth.GLOBAL_02: 1,
                PROMISGlobalHealth.GLOBAL_03: 1,
                PROMISGlobalHealth.GLOBAL_04: 1,
                PROMISGlobalHealth.GLOBAL_05: 1,
                PROMISGlobalHealth.GLOBAL_06: 1,
                PROMISGlobalHealth.GLOBAL_07_RC: 10,
                PROMISGlobalHealth.GLOBAL_08_R: 1,
                PROMISGlobalHealth.GLOBAL_09_R: 1,
                PROMISGlobalHealth.GLOBAL_10_R: 1,
                "metadata": {"answers": []},
            }
        )
        primitive: PROMISGlobalHealth = PROMISGlobalHealth.from_dict(COMMON_FIELDS)
        module = PROMISGlobalHealthModule()
        module.calculate(primitive)

        global_7_rc = 1
        self.assertEqual(global_7_rc, primitive.global07rc)
        self.assertEqual(21.2, primitive.mentalHealthValue)
        self.assertEqual(16.2, primitive.physicalHealthValue)

    def test_success_calculate_result_case_3(self):
        COMMON_FIELDS.update(
            {
                PROMISGlobalHealth.GLOBAL_01: 2,
                PROMISGlobalHealth.GLOBAL_02: 3,
                PROMISGlobalHealth.GLOBAL_03: 2,
                PROMISGlobalHealth.GLOBAL_04: 3,
                PROMISGlobalHealth.GLOBAL_05: 2,
                PROMISGlobalHealth.GLOBAL_06: 3,
                PROMISGlobalHealth.GLOBAL_07_RC: 5,
                PROMISGlobalHealth.GLOBAL_08_R: 2,
                PROMISGlobalHealth.GLOBAL_09_R: 3,
                PROMISGlobalHealth.GLOBAL_10_R: 2,
                "metadata": {"answers": []},
            }
        )
        primitive: PROMISGlobalHealth = PROMISGlobalHealth.from_dict(COMMON_FIELDS)
        module = PROMISGlobalHealthModule()
        module.calculate(primitive)

        global_7_rc = 3
        self.assertEqual(global_7_rc, primitive.global07rc)
        self.assertEqual(38.8, primitive.mentalHealthValue)
        self.assertEqual(34.9, primitive.physicalHealthValue)

    def test_failure_missing_required_fields(self):
        self._assign_primitive_values()
        required_fields = [
            PROMISGlobalHealth.GLOBAL_01,
            PROMISGlobalHealth.GLOBAL_02,
            PROMISGlobalHealth.GLOBAL_03,
            PROMISGlobalHealth.GLOBAL_04,
            PROMISGlobalHealth.GLOBAL_05,
            PROMISGlobalHealth.GLOBAL_06,
            PROMISGlobalHealth.GLOBAL_07_RC,
            PROMISGlobalHealth.GLOBAL_08_R,
            PROMISGlobalHealth.GLOBAL_09_R,
            PROMISGlobalHealth.GLOBAL_10_R,
        ]
        for field in required_fields:
            az_data = copy.deepcopy(COMMON_FIELDS)
            az_data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                PROMISGlobalHealth.from_dict(az_data)
