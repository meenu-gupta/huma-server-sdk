from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class SignOutEvent(BaseEvent, Convertible):
    def __init__(
        self,
        id=None,
        user_id=None,
        refresh_token=None,
        device_agent=None,
        update_date_time=None,
        create_date_time=None,
    ):
        self.id = id
        self.userId = user_id
        self.refresh_token = refresh_token
        self.device_agent = device_agent
        self.update_date_time = update_date_time
        self.create_date_time = create_date_time


class SignOutEventV1(BaseEvent, Convertible):
    def __init__(self, user_id=None, device_push_id=None, voip_device_push_id=None):
        self.userId = user_id
        self.device_push_id = device_push_id
        self.voip_device_push_id = voip_device_push_id
