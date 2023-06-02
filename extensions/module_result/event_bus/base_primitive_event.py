from extensions.module_result.models.primitives import Primitive
from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible
from sdk.common.utils.validators import remove_none_values


class BasePrimitiveEvent(BaseEvent, Convertible):
    MODULE_CONFIG_BODY = "moduleConfigBody"
    KEY_ACTIONS = "keyActions"

    def __init__(
        self,
        primitive_name,
        module_id,
        user_id,
        deployment_id,
        device_name,
        module_config_id=None,
        module_result_id=None,
        **kwargs
    ):
        self.primitive_name = primitive_name
        self.module_id = module_id
        self.module_result_id = module_result_id
        self.user_id = user_id
        self.deployment_id = deployment_id
        self.device_name = device_name
        self.module_config_id = module_config_id
        self.kwargs = kwargs

    @classmethod
    def from_primitive(cls, primitive: Primitive):
        return cls.from_dict(
            remove_none_values(
                {
                    **primitive.to_dict(include_none=False),
                    "primitiveName": primitive.class_name,
                }
            )
        )
