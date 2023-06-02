from sdk.common.adapter.event_bus_adapter import BaseEvent


class PostUnlinkProxyUserEvent(BaseEvent):
    def __init__(self, user_id: str):
        self.user_id = user_id
