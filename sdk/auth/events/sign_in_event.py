from sdk.common.adapter.event_bus_adapter import BaseEvent


class SignInEvent(BaseEvent):
    def __init__(self, user_id=None):
        self.user_id = user_id
