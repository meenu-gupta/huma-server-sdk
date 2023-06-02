from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class BaseAuthorizationEvent(BaseEvent, Convertible):
    def __init__(
        self,
        module_id,
        user_id,
        deployment_id,
        device_name,
        module_config_id=None,
        **kwargs
    ):
        self.module_id = module_id
        self.user_id = user_id
        self.deployment_id = deployment_id
        self.device_name = device_name
        self.module_config_id = module_config_id
        self.kwargs = kwargs
