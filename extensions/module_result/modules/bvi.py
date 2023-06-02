from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import InvalidModuleResultException
from extensions.module_result.models.primitives import (
    BodyMeasurement,
    Primitive,
    Questionnaire,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.visualizer import BodyMeasurementHTMLVisualizer


class BVIModule(Module):
    moduleId = "BodyMeasurement"
    primitives = [Questionnaire, BodyMeasurement]
    preferredUnitEnabled = True
    visualizer = BodyMeasurementHTMLVisualizer

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        if not primitives:
            return

        for primitive in primitives:
            if type(primitive) != BodyMeasurement:
                continue

            if primitive.waistCircumference and primitive.hipCircumference:
                primitive.waistToHipRatio = (
                    primitive.waistCircumference / primitive.hipCircumference
                )

        super().preprocess(primitives, user)

    def validate_module_result(self, module_result: list[Primitive]):
        invalid_primitives = [
            str(p) for p in module_result if type(p) not in self.primitives
        ]
        if invalid_primitives:
            raise InvalidModuleResultException(
                f"Invalid primitives [{invalid_primitives}]"
            )

        valid_primitives = self.primitives.copy()
        for primitive in module_result:
            try:
                valid_primitives.remove(type(primitive))
            except Exception:
                invalid_primitives.append(str(primitive))

        if invalid_primitives:
            raise InvalidModuleResultException(
                f"Too many primitives for module {self.moduleId}: [{[str(p) for p in module_result]}]"
            )
