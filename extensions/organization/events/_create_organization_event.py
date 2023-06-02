from dataclasses import dataclass
from datetime import datetime

from sdk.common.adapter.event_bus_adapter import BaseEvent


@dataclass
class PostCreateOrganizationEvent(BaseEvent):
    organization_id: str
    user_id: str
    date: datetime
