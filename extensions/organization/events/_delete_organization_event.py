from dataclasses import dataclass

from sdk.common.adapter.event_bus_adapter import BaseEvent


@dataclass
class PostDeleteOrganizationEvent(BaseEvent):
    organization_id: str
    user_id: str
