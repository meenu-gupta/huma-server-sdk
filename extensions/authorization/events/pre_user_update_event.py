from sdk.common.adapter.event_bus_adapter import BaseEvent


class PreUserProfileUpdateEvent(BaseEvent):
    def __init__(self, user=None, previous_state=None):
        from extensions.authorization.models.user import User

        self.user: User = user
        self.previous_state: User = previous_state
