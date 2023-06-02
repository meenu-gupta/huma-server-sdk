from extensions.deployment.models.deployment import Label
from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class PostAssignLabelEvent(BaseEvent, Convertible):
    def __init__(self, labels: list[Label], user_ids: list[str], assignee_id: str):
        self.labels = labels
        self.user_ids = user_ids
        self.assignee_id = assignee_id
