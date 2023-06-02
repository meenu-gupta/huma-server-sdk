from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class CheckAuthAttributesEvent(BaseEvent, Convertible):
    def __init__(
        self,
        user_id=None,
        client_id=None,
        project_id=None,
    ):
        self.user_id = user_id
        self.client_id = client_id
        self.project_id = project_id
