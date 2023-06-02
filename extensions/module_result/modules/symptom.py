from pathlib import Path

from extensions.authorization.models.user import User, UnseenFlags
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Symptom,
    Primitive,
    ComplexSymptomValue,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import read_json_file
from .module import Module
from .visualizer import SymptomHTMLVisualizer

NAME = ComplexSymptomValue.NAME
SEVERITY = ComplexSymptomValue.SEVERITY
SEVERITIES = "severities"


class SymptomModule(Module):
    moduleId = "Symptom"
    primitives = [Symptom]
    ragEnabled = True
    visualizer = SymptomHTMLVisualizer

    def preprocess(self, primitives: list[Primitive], user: User):
        [self._validate_severity_range(p) for p in primitives]
        super().preprocess(primitives, user)

    def _validate_severity_range(self, primitive: Primitive):
        complex_values: list[ComplexSymptomValue] = primitive.complexValues
        complex_symptoms = self.config.get_config_body().get("complexSymptoms", None)

        if not (complex_symptoms and complex_values):
            return

        symptom_severities = dict()
        for symptom in complex_symptoms:
            severities = [x.get(SEVERITY) for x in symptom.get("scale", [])]
            symptom_severities[symptom.get(NAME)] = severities

        for value in complex_values:
            if value.name not in symptom_severities:
                raise ConvertibleClassValidationError(
                    f"symptom {value.name} does not exist in config"
                )

            if value.severity not in symptom_severities[value.name]:
                raise ConvertibleClassValidationError(
                    f"symptom {value.name} severity value {value.severity} is out of range"
                )

    def get_validation_schema(self):
        return read_json_file("./schemas/symptom_schema.json", Path(__file__).parent)

    def get_threshold_data(
        self,
        target_primitive: Symptom,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        threshold_data = {}
        calculated_threshold_data = self.calculate_threshold(
            target_primitive, module_config, primitives
        )
        if calculated_threshold_data:
            color_data, severities = calculated_threshold_data
            threshold_data.update({"color": color_data, "severities": list(severities)})

        return threshold_data

    def validate_module_config(self, module_config):
        pass

    def calculate_threshold(
        self,
        primitive: Symptom,
        module_config: ModuleConfig,
        primitives: list[Primitive],
    ):
        complex_values: list[ComplexSymptomValue] = primitive.complexValues
        complex_symptoms = (module_config.configBody or {}).get("complexSymptoms", None)
        if not (complex_symptoms and module_config.ragThresholds):
            return

        severities = list()
        color_dict = {}
        for answer in complex_values:
            valid_thresholds = filter(
                lambda x: x.fieldName == answer.name, module_config.ragThresholds
            )
            for valid_threshold in valid_thresholds:
                for threshold_range in valid_threshold.thresholdRange:
                    if not self._match_threshold(threshold_range, answer.severity):
                        continue

                    severities.append(valid_threshold.severity)
                    color_dict.update(
                        {valid_threshold.fieldName: valid_threshold.color}
                    )

        if color_dict:
            return color_dict, severities

    def apply_overall_flags_logic(self, primitives: list[Primitive]):
        if not self.config.ragThresholds and primitives:
            symptom_count = sum(len(p.complexValues or []) for p in primitives)
            primitives[0].flags = {
                UnseenFlags.RED: 0,
                UnseenFlags.AMBER: 0,
                UnseenFlags.GRAY: symptom_count,
            }
