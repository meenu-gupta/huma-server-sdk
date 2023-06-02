import unittest
from unittest.mock import MagicMock

from extensions.module_result.models.module_config import (
    CustomRagThreshold,
    ModuleConfig,
    RagThreshold,
    RagThresholdType,
    ThresholdRange,
)
from extensions.module_result.models.primitives import (
    Weight,
    BloodPressure,
    ChangeDirection,
    HeartRate,
)
from extensions.module_result.models.primitives.primitive_oxford_knee import (
    OxfordKneeScore,
    LegAffected,
)
from extensions.module_result.modules import (
    BloodPressureModule,
    OxfordKneeScoreQuestionnaireModule,
    HeartRateModule,
)
from extensions.module_result.modules.weight import WeightModule
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

COLOR = RagThreshold.COLOR
DIRECTION = RagThreshold.DIRECTION
VALUE = Weight.VALUE


def sample_module_config() -> dict:
    return {
        "moduleId": "BMI",
        "moduleName": "BMI",
        "ragThresholds": [
            {
                "color": "green",
                "severity": 1,
                "fieldName": "value",
                "type": "VALUE",
                "thresholdRange": [{"minValue": 10, "maxValue": 19}],
                "enabled": True,
            }
        ],
    }


class BaseThresholdTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = MagicMock()
        self.server_config = MagicMock()

        def configure_with_binder(binder: inject.Binder):
            binder.bind(PhoenixServerConfig, self.server_config)

        inject.clear_and_configure(config=configure_with_binder)


class ApplyThresholdsTestCase(BaseThresholdTestCase):
    @property
    def module(self):
        return WeightModule()

    def module_config(
        self,
        rag_type: RagThresholdType,
        threshold_range_low: list[ThresholdRange],
        threshold_range_high: list[ThresholdRange],
    ):
        return ModuleConfig(
            moduleId="Weight",
            moduleName="Weight",
            ragThresholds=[
                RagThreshold(
                    color="green",
                    severity=1,
                    fieldName="value",
                    type=rag_type,
                    thresholdRange=threshold_range_low,
                    enabled=True,
                ),
                RagThreshold(
                    color="amber",
                    severity=2,
                    fieldName="value",
                    type=rag_type,
                    thresholdRange=threshold_range_high,
                    enabled=True,
                ),
            ],
        )

    def test_apply_threshold_value_type(self):
        primitive = Weight(value=112)

        module_config = self.module_config(
            RagThresholdType.VALUE,
            [ThresholdRange(minValue=110, maxValue=119)],
            [ThresholdRange(minValue=120, maxValue=130)],
        )
        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "green")

        primitive = Weight(value=125)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "amber")

    def test_apply_threshold_type_change_number(self):
        module_config = self.module_config(
            RagThresholdType.CHANGE_NUMBER,
            [ThresholdRange(minValue=10, maxValue=19)],
            [ThresholdRange(minValue=20, maxValue=30)],
        )

        primitive = Weight(value=110)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "green")

        primitive = Weight(value=125)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "amber")

    def test_apply_threshold_type_change_percent(self):
        module_config = self.module_config(
            RagThresholdType.CHANGE_NUMBER,
            [ThresholdRange(minValue=-5, maxValue=5)],
            [
                ThresholdRange(minValue=-20, maxValue=-6),
                ThresholdRange(minValue=6, maxValue=20),
            ],
        )

        primitive = Weight(value=103)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "green")

        primitive = Weight(value=112)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "amber")

        primitive = Weight(value=95)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "green")

        primitive = Weight(value=84)

        threshold = self.module.calculate_threshold(
            primitive, module_config, [Weight(value=100)]
        )
        self.assertEqual(threshold[VALUE].color, "amber")

    def test_failure_rag_threshold_wrong_fieldname(self):
        with self.assertRaises(InvalidRequestException):
            module_config = sample_module_config()
            module_config["ragThresholds"][0]["fieldName"] = "wrong_filed_name"
            ModuleConfig.from_dict(module_config)

    def test_failure_rag_threshold_wrong_moduleid(self):
        with self.assertRaises(InvalidRequestException):
            module_config = sample_module_config()
            module_config["moduleId"] = "wrong_module_name"
            ModuleConfig.from_dict(module_config)


class MultipleFieldsThresholdTestCase(BaseThresholdTestCase):
    @property
    def module(self):
        return BloodPressureModule()

    def module_config(
        self,
        rag_type: RagThresholdType,
        threshold_range_low: list[ThresholdRange],
        threshold_range_high: list[ThresholdRange],
    ):
        return ModuleConfig(
            moduleId="BloodPressure",
            moduleName="BloodPressure",
            ragThresholds=[
                RagThreshold(
                    color="green",
                    severity=1,
                    fieldName="diastolicValue",
                    type=rag_type,
                    thresholdRange=threshold_range_low,
                    enabled=True,
                ),
                RagThreshold(
                    color="amber",
                    severity=2,
                    fieldName="diastolicValue",
                    type=rag_type,
                    thresholdRange=threshold_range_high,
                    enabled=True,
                ),
                RagThreshold(
                    color="yellow",
                    severity=3,
                    fieldName="diastolicValue",
                    type=rag_type,
                    thresholdRange=threshold_range_high,
                    enabled=True,
                ),
                RagThreshold(
                    color="pink",
                    severity=1,
                    fieldName="systolicValue",
                    type=rag_type,
                    thresholdRange=threshold_range_low,
                    enabled=True,
                ),
                RagThreshold(
                    color="red",
                    severity=2,
                    fieldName="systolicValue",
                    type=rag_type,
                    thresholdRange=threshold_range_high,
                    enabled=True,
                ),
            ],
        )

    def test_multiple_field_threshold(self):
        primitive = BloodPressure(diastolicValue=80, systolicValue=100)

        module_config = self.module_config(
            rag_type=RagThresholdType.VALUE,
            threshold_range_low=[ThresholdRange(minValue=60, maxValue=110)],
            threshold_range_high=[ThresholdRange(minValue=111, maxValue=130)],
        )

        threshold = self.module.get_threshold_data(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=65, systolicValue=110)],
        )

        self.assertDictEqual(
            threshold[BloodPressure.DIASTOLIC_VALUE],
            {
                COLOR: "green",
                DIRECTION: ChangeDirection.INCREASED.value,
                RagThreshold.SEVERITY: 1,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )
        self.assertDictEqual(
            threshold[BloodPressure.SYSTOLIC_VALUE],
            {
                COLOR: "pink",
                DIRECTION: ChangeDirection.DECREASED.value,
                RagThreshold.SEVERITY: 1,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )

    def test_single_field_threshold(self):
        primitive = BloodPressure(diastolicValue=80)

        module_config = self.module_config(
            rag_type=RagThresholdType.VALUE,
            threshold_range_low=[ThresholdRange(minValue=60, maxValue=110)],
            threshold_range_high=[ThresholdRange(minValue=111, maxValue=130)],
        )

        threshold = self.module.get_threshold_data(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=50, systolicValue=90)],
        )

        self.assertDictEqual(
            threshold[BloodPressure.DIASTOLIC_VALUE],
            {
                COLOR: "green",
                DIRECTION: ChangeDirection.INCREASED.value,
                RagThreshold.SEVERITY: 1,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )
        self.assertEqual(threshold[BloodPressure.SYSTOLIC_VALUE], {})

    def test_single_field_threshold_custom_rag(self):
        primitive = BloodPressure(diastolicValue=80)

        module_config = self.module_config(
            rag_type=RagThresholdType.VALUE,
            threshold_range_low=[ThresholdRange(minValue=60, maxValue=110)],
            threshold_range_high=[ThresholdRange(minValue=111, maxValue=130)],
        )
        for rag in module_config.ragThresholds:
            rag.isCustom = True

        threshold = self.module.get_threshold_data(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=50, systolicValue=90)],
        )

        self.assertDictEqual(
            threshold[BloodPressure.DIASTOLIC_VALUE],
            {
                COLOR: "green",
                DIRECTION: ChangeDirection.INCREASED.value,
                RagThreshold.SEVERITY: 1,
                CustomRagThreshold.IS_CUSTOM: True,
            },
        )
        self.assertEqual(threshold[BloodPressure.SYSTOLIC_VALUE], {})

    def test_severity_still_has_precedence_for_individual_fields(self):
        primitive = BloodPressure(diastolicValue=115)

        module_config = self.module_config(
            rag_type=RagThresholdType.VALUE,
            threshold_range_low=[ThresholdRange(minValue=60, maxValue=110)],
            threshold_range_high=[ThresholdRange(minValue=111, maxValue=130)],
        )

        threshold = self.module.get_threshold_data(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=65, systolicValue=105)],
        )
        self.assertDictEqual(
            threshold[BloodPressure.DIASTOLIC_VALUE],
            {
                COLOR: "yellow",
                DIRECTION: ChangeDirection.INCREASED.value,
                RagThreshold.SEVERITY: 3,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )
        self.assertDictEqual(threshold[BloodPressure.SYSTOLIC_VALUE], {})

    def test_threshold_type_change_number_for_multiple_fields(self):
        module_config = self.module_config(
            RagThresholdType.CHANGE_NUMBER,
            [ThresholdRange(minValue=30, maxValue=40)],
            [ThresholdRange(minValue=41, maxValue=60)],
        )

        primitive = BloodPressure(diastolicValue=90, systolicValue=110)

        threshold = self.module.calculate_threshold(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=40, systolicValue=70)],
        )

        self.assertEqual(threshold[BloodPressure.DIASTOLIC_VALUE].color, "yellow")
        self.assertEqual(threshold[BloodPressure.SYSTOLIC_VALUE].color, "pink")

    def test_threshold_type_change_number_for_primitive_with_missing_value(self):
        module_config = self.module_config(
            RagThresholdType.CHANGE_NUMBER,
            [ThresholdRange(minValue=30, maxValue=40)],
            [ThresholdRange(minValue=41, maxValue=60)],
        )

        primitive = BloodPressure(diastolicValue=90, systolicValue=110)

        threshold = self.module.calculate_threshold(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=50)],
        )

        self.assertEqual(threshold[BloodPressure.DIASTOLIC_VALUE].color, "green")

    def _calculate_sample_threshold(self):
        primitive = BloodPressure(diastolicValue=80, systolicValue=100)

        module_config = self.module_config(
            rag_type=RagThresholdType.VALUE,
            threshold_range_low=[ThresholdRange(minValue=60, maxValue=110)],
            threshold_range_high=[ThresholdRange(minValue=111, maxValue=130)],
        )

        return self.module.get_threshold_data(
            primitive,
            module_config,
            [BloodPressure(diastolicValue=50, systolicValue=90)],
        )

    def test_get_threshold_data(self):
        threshold = self._calculate_sample_threshold()
        self.assertEqual(2, len(threshold["severities"]))


class MultipleFieldsOxfordKneeScoreThresholdTestCase(BaseThresholdTestCase):
    @property
    def module(self):
        return OxfordKneeScoreQuestionnaireModule()

    def module_config(self):
        rag_threshold_dicts = [
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 3,
                RagThreshold.RANGE: [{"maxValue": 19.0}],
                COLOR: "#FBCCD7",
                RagThreshold.FIELD_NAME: OxfordKneeScore.LEFT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 3,
                RagThreshold.RANGE: [{"maxValue": 19.0}],
                COLOR: "#FBCCD7",
                RagThreshold.FIELD_NAME: OxfordKneeScore.RIGHT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 2,
                RagThreshold.RANGE: [{"minValue": 20.0, "maxValue": 29.0}],
                COLOR: "#FFDA9F",
                RagThreshold.FIELD_NAME: OxfordKneeScore.LEFT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 2,
                RagThreshold.RANGE: [{"minValue": 20.0, "maxValue": 29.0}],
                COLOR: "#FFDA9F",
                RagThreshold.FIELD_NAME: OxfordKneeScore.RIGHT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 1,
                RagThreshold.RANGE: [{"minValue": 30.0, "maxValue": 39.0}],
                COLOR: "#CBEBF0",
                RagThreshold.FIELD_NAME: OxfordKneeScore.LEFT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
            {
                RagThreshold.TYPE: RagThresholdType.VALUE.value,
                RagThreshold.SEVERITY: 1,
                RagThreshold.RANGE: [{"minValue": 30.0, "maxValue": 39.0}],
                COLOR: "#CBEBF0",
                RagThreshold.FIELD_NAME: OxfordKneeScore.RIGHT_KNEE_SCORE,
                RagThreshold.ENABLED: True,
            },
        ]
        rag_thresholds = [
            RagThreshold.from_dict(rag_dict) for rag_dict in rag_threshold_dicts
        ]
        return ModuleConfig(
            moduleId=OxfordKneeScoreQuestionnaireModule.moduleId,
            moduleName=OxfordKneeScore.__name__,
            ragThresholds=rag_thresholds,
        )

    def test_multiple_field_knee_score_threshold(self):
        knee_score_data = {
            OxfordKneeScore.LEG_AFFECTED: LegAffected.BOTH,
            OxfordKneeScore.RIGHT_KNEE_SCORE: 14,
            OxfordKneeScore.LEFT_KNEE_SCORE: 25,
        }

        primitive = OxfordKneeScore(**knee_score_data)

        module_config = self.module_config()

        threshold = self.module.get_threshold_data(
            primitive,
            module_config,
            [],
        )

        self.assertDictEqual(
            threshold[OxfordKneeScore.LEFT_KNEE_SCORE],
            {
                COLOR: "#FFDA9F",
                RagThreshold.SEVERITY: 2,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )
        self.assertDictEqual(
            threshold[OxfordKneeScore.RIGHT_KNEE_SCORE],
            {
                COLOR: "#FBCCD7",
                RagThreshold.SEVERITY: 3,
                CustomRagThreshold.IS_CUSTOM: False,
            },
        )

        self.assertEqual(2, len(threshold["severities"]))


class ChangeDirectionTestCase(BaseThresholdTestCase):
    def setUp(self):
        super().setUp()

        self.config = ModuleConfig(id="testModuleId", moduleId="HeartRate")

    def test_calculate_change_direction_min_calculated(self):
        with HeartRateModule().configure(self.config) as module:
            primitive = HeartRate(value=99)
            result = module.calculate_change_direction(
                primitive, [primitive], HeartRate.VALUE
            )
            self.assertEqual(ChangeDirection.NOCHANGE.value, result)

    def test_calculate_change_direction__exact_value_str_no_calculated(self):
        with HeartRateModule().configure(self.config) as module:
            primitive = HeartRate(classification="AF")
            result = module.calculate_change_direction(
                primitive, [primitive], HeartRate.CLASSIFICATION
            )
            self.assertIsNone(result)
