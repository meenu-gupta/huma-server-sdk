from sdk.common.adapter.event_bus_adapter import BaseEvent


class PostUserOffBoardEvent(BaseEvent):
    def __init__(self, user_id: str, detail: str):
        self.user_id = user_id
        self.offboarding_detail = detail
