from extensions.module_result.models.module_config import ModuleConfig, RagThreshold
from extensions.module_result.models.primitives import BloodPressure, Primitive
from .module import Module
from .visualizer import BloodPressureHTMLVisualizer


class BloodPressureModule(Module):
    moduleId = "BloodPressure"
    primitives = [BloodPressure]
    ragEnabled = True
    visualizer = BloodPressureHTMLVisualizer

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        thresholds = super(BloodPressureModule, self).get_threshold_data(
            target_primitive, module_config, primitives
        )

        severities = [
            primitive[RagThreshold.SEVERITY]
            for name, primitive in thresholds.items()
            if name in [BloodPressure.DIASTOLIC_VALUE, BloodPressure.SYSTOLIC_VALUE]
            and RagThreshold.SEVERITY in primitive
        ]
        if severities:
            thresholds.update({"severities": severities})

        return thresholds
