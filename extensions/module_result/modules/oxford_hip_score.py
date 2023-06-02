from extensions.module_result.models.module_config import ModuleConfig, RagThreshold
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_oxford_hip import (
    OxfordHipScore,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.oxford_hip_score_calculator import (
    OxfordHipScoreCalculator,
)
from extensions.module_result.modules.visualizer import OxfordHipScoreHTMLVisualizer


class OxfordHipScoreQuestionnaireModule(Module):
    moduleId = "OxfordHipScore"
    primitives = [OxfordHipScore]
    ragEnabled = True
    calculator = OxfordHipScoreCalculator
    visualizer = OxfordHipScoreHTMLVisualizer

    def calculate(self, primitive: OxfordHipScore):
        self.calculator().calculate(primitive)

    def validate_config_body(self, module_config: ModuleConfig):
        pass

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        thresholds = super(OxfordHipScoreQuestionnaireModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )

        severities = [
            primitive[RagThreshold.SEVERITY]
            for name, primitive in thresholds.items()
            if name in [OxfordHipScore.LEFT_HIP_SCORE, OxfordHipScore.RIGHT_HIP_SCORE]
            if RagThreshold.SEVERITY in primitive
        ]
        if severities:
            thresholds.update({"severities": severities})

        return thresholds
