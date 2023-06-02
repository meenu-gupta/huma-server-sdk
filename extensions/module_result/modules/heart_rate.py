from pathlib import Path

from jsonschema import validate

from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import HeartRate
from sdk.common.utils.validators import read_json_file


class HeartRateModule(Module):
    moduleId = "HeartRate"
    primitives = [HeartRate]
    ragEnabled = True

    def get_validation_schema(self) -> dict:
        return read_json_file("./schemas/heart_rate_schema.json", Path(__file__).parent)

    def validate_config_body(self, module_config: ModuleConfig):
        schema = self.get_validation_schema()
        if schema:
            if not module_config.configBody:
                return
            validate(module_config.configBody, schema=schema)
        else:
            if module_config.configBody:
                module_config.configBody = {}
