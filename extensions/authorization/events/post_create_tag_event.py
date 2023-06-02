from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class PostCreateTagEvent(BaseEvent, Convertible):
    def __init__(self, tags: dict, user_id: str, author_id: str):
        self.tags = tags
        self.user_id = user_id
        self.author_id = author_id
