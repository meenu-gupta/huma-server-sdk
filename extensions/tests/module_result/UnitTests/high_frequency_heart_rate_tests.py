from unittest.mock import MagicMock

from extensions.module_result.common.models import MultipleValuesData
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import HighFrequencyHeartRate
from extensions.module_result.modules import HighFrequencyHeartRateModule
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class HighFrequencyHeartRateTestCase(PrimitiveTestCase):
    def test_success_creation_multiple_value(self):
        COMMON_FIELDS["value"] = 0
        COMMON_FIELDS["dataType"] = "MULTIPLE_VALUE"
        COMMON_FIELDS["multipleValues"] = [
            {
                "id": "5b5279d1e303d394db6ea0f8",
                "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 57.02},
                "d": "2019-06-30T00:00:00Z",
            },
            {
                "id": "5b5279d1e303d394db6ea134",
                "p": {"0": 69.47, "15": 69.47, "30": 68.46, "45": 69.45},
                "d": "2019-06-30T01:00:00Z",
            },
        ]
        primitive = HighFrequencyHeartRate.create_from_dict(
            COMMON_FIELDS, name="HighFrequencyHeartRate"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(
            primitive.dataType, HighFrequencyHeartRate.DataType.MULTIPLE_VALUE
        )

    def test_success_creation_ppg_value(self):
        COMMON_FIELDS["value"] = 0
        COMMON_FIELDS["dataType"] = "PPG_VALUE"
        COMMON_FIELDS["rawDataObject"] = {
            "bucket": "bucket",
            "key": "key",
            "region": "eu",
        }
        primitive = HighFrequencyHeartRate.create_from_dict(
            COMMON_FIELDS, name="HighFrequencyHeartRate"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.dataType, HighFrequencyHeartRate.DataType.PPG_VALUE)

    def test_apply_overall_flags_logic_multiple_values(self):
        sample_primitive = MagicMock(
            **{
                HighFrequencyHeartRate.DATA_TYPE: HighFrequencyHeartRate.DataType.MULTIPLE_VALUE,
                HighFrequencyHeartRate.MULTIPLE_VALUES: [
                    MultipleValuesData.from_dict(
                        {
                            "d": "2021-09-13T09:00:00.000000Z",
                            "p": {"0": 77, "15": 95, "30": 86, "45": 100},
                        }
                    ),
                    MultipleValuesData.from_dict(
                        {
                            "d": "2021-09-13T10:00:00.000000Z",
                            "p": {"0": 73, "15": 0, "30": 0, "45": 0},
                        }
                    ),
                ],
            }
        )
        primitives = [sample_primitive, sample_primitive]
        module = HighFrequencyHeartRateModule()
        module.config = MagicMock(spec_set=ModuleConfig)
        module.config.ragThresholds = None
        module.apply_overall_flags_logic(primitives)
        expected_res = {"red": 0, "amber": 0, "gray": 10}
        self.assertEqual(expected_res, primitives[0].flags)

    def test_apply_overall_flags_logic_single_value(self):
        primitives = [
            MagicMock(
                **{
                    HighFrequencyHeartRate.DATA_TYPE: HighFrequencyHeartRate.DataType.SINGLE_VALUE,
                    HighFrequencyHeartRate.VALUE: 90,
                }
            ),
            MagicMock(
                **{
                    HighFrequencyHeartRate.DATA_TYPE: HighFrequencyHeartRate.DataType.SINGLE_VALUE,
                    HighFrequencyHeartRate.VALUE: 0,
                }
            ),
        ]
        module = HighFrequencyHeartRateModule()
        module.config = MagicMock(spec_set=ModuleConfig)
        module.config.ragThresholds = None
        module.apply_overall_flags_logic(primitives)
        expected_res = {"red": 0, "amber": 0, "gray": 1}
        self.assertEqual(expected_res, primitives[0].flags)

    def test_apply_overall_flags_logic_ppg_value(self):
        primitives = [
            MagicMock(
                **{
                    HighFrequencyHeartRate.DATA_TYPE: HighFrequencyHeartRate.DataType.PPG_VALUE,
                    HighFrequencyHeartRate.VALUE: 85,
                }
            ),
            MagicMock(
                **{
                    HighFrequencyHeartRate.DATA_TYPE: HighFrequencyHeartRate.DataType.PPG_VALUE,
                    HighFrequencyHeartRate.VALUE: 0,
                }
            ),
        ]
        module = HighFrequencyHeartRateModule()
        module.config = MagicMock(spec_set=ModuleConfig)
        module.config.ragThresholds = None
        module.apply_overall_flags_logic(primitives)
        expected_res = {"red": 0, "amber": 0, "gray": 1}
        self.assertEqual(expected_res, primitives[0].flags)

    def test_failure_wrong_data_type(self):
        COMMON_FIELDS["value"] = 90
        COMMON_FIELDS["dataType"] = "dummy_data_type"
        with self.assertRaises(ConvertibleClassValidationError):
            HighFrequencyHeartRate.create_from_dict(
                COMMON_FIELDS, name="HighFrequencyHeartRate"
            )
