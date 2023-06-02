from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class PostCreateAuthorizationBatchEvent(BaseEvent, Convertible):
    def __init__(
        self,
        primitives,
        user_id,
        module_id,
        module_config_id,
        deployment_id,
        device_name,
        start_date_time,
    ):
        self.primitives = primitives
        self.user_id = user_id
        self.module_id = module_id
        self.module_config_id = module_config_id
        self.deployment_id = deployment_id
        self.device_name = device_name
        self.start_date_time = start_date_time
