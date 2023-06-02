import unittest
from unittest.mock import patch, MagicMock

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Symptom
from extensions.module_result.modules import SymptomModule
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import PhoenixServerConfig

PATH = "extensions.module_result.modules.symptom"


class MockRagThreshold:
    instance = MagicMock()
    fieldName = "some_name"
    thresholdRange = [MagicMock()]
    severity = 0
    color = "some_color"


class MockComplexValue:
    def __init__(self, severity: int = 1, name: str = "Persistent cough"):
        self.severity = severity
        self.name = name

    instance = MagicMock()


sample_config = {
    "complexSymptoms": [
        {
            "name": "Persistent cough",
            "scale": [
                {"severity": 1, "value": "Mild"},
                {"severity": 2, "value": "Moderate"},
            ],
        }
    ]
}


class SymptomModuleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = MagicMock()
        self.module_config = ModuleConfig(
            moduleId=SymptomModule.__name__, configBody=sample_config
        )

        def configure_with_binder(binder: inject.Binder):
            binder.bind(PhoenixServerConfig, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    @patch(f"{PATH}.read_json_file")
    def test_get_validation_schema(self, read_json_file):
        module = SymptomModule()
        module.get_validation_schema()
        read_json_file.assert_called_once()

    @patch(f"{PATH}.SymptomModule.calculate_threshold")
    def test_get_threshold_data(self, calculate_threshold):
        target_primitive = MagicMock()
        module_config = MagicMock()
        primitives = [target_primitive]
        module = SymptomModule()
        calculate_threshold.return_value = MagicMock(), MagicMock()
        module.get_threshold_data(target_primitive, module_config, primitives)
        calculate_threshold.assert_called_with(
            target_primitive, module_config, primitives
        )

    @patch(f"{PATH}.SymptomModule._match_threshold")
    def test_calculate_threshold(self, match_threshold):
        primitive = MagicMock()
        value = MagicMock()
        value.name = "some_name"
        primitive.complexValues = [value]
        module_config = MagicMock()
        rag_threshold = MockRagThreshold()
        module_config.ragThresholds = [rag_threshold]
        module = SymptomModule()
        module.calculate_threshold(primitive, module_config, [primitive])
        match_threshold.assert_called_with(
            rag_threshold.thresholdRange[0], value.severity
        )

    @patch(f"{PATH}.SymptomModule._validate_severity_range")
    def test_validate_severity(self, validate_severity_range):
        primitive = MagicMock()
        primitive.complexValues = [MockComplexValue()]
        with SymptomModule().configure(self.module_config) as module:
            module.preprocess([primitive], MagicMock())
            validate_severity_range.assert_called_with(primitive)

    def test_success_validate_severity(self):
        primitive = MagicMock()
        primitive.complexValues = [MockComplexValue()]
        with SymptomModule().configure(self.module_config) as module:
            module._validate_severity_range(primitive)

    def test_failure_validate_severity_invalid_symptom_name(self):
        primitive = MagicMock()
        primitive.complexValues = [MockComplexValue(name="Some name")]
        with SymptomModule().configure(self.module_config) as module:
            with self.assertRaises(ConvertibleClassValidationError):
                module._validate_severity_range(primitive)

    def test_failure_validate_severity_invalid_severity(self):
        primitive = MagicMock()
        primitive.complexValues = [MockComplexValue(severity=6)]
        with SymptomModule().configure(self.module_config) as module:
            with self.assertRaises(ConvertibleClassValidationError):
                module._validate_severity_range(primitive)

    def test_apply_overall_flags_logic(self):
        sample_primitive = MagicMock(**{Symptom.COMPLEX_VALUES: [1, 2, 3]})
        primitives = [sample_primitive, sample_primitive]
        module = SymptomModule()
        module.config = MagicMock(spec_set=ModuleConfig)
        module.config.ragThresholds = None
        module.apply_overall_flags_logic(primitives)
        expected_res = {"red": 0, "amber": 0, "gray": 6}
        self.assertEqual(expected_res, primitives[0].flags)

    def test_apply_overall_flags_logic_with_none(self):
        sample_primitive = MagicMock(**{Symptom.COMPLEX_VALUES: None})
        primitives = [sample_primitive, sample_primitive]
        module = SymptomModule()
        module.config = MagicMock(spec_set=ModuleConfig)
        module.config.ragThresholds = None
        module.apply_overall_flags_logic(primitives)
        expected_res = {"red": 0, "amber": 0, "gray": 0}
        self.assertEqual(expected_res, primitives[0].flags)


if __name__ == "__main__":
    unittest.main()
