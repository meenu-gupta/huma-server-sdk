from pathlib import Path

from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import SensorCapture
from sdk.common.utils.validators import read_json_file


class BreathingModule(Module):
    moduleId = "Breathing"
    primitives = [SensorCapture]

    def get_validation_schema(self) -> dict:
        return read_json_file("./schemas/breathing_schema.json", Path(__file__).parent)
