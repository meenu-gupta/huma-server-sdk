from dataclasses import dataclass

from sdk.common.adapter.event_bus_adapter import BaseEvent


@dataclass
class GetUserBadgesEvent(BaseEvent):
    user_id: str
