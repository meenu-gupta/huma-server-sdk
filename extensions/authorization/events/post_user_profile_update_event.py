from sdk.common.adapter.event_bus_adapter import BaseEvent


class PostUserProfileUpdateEvent(BaseEvent):
    def __init__(self, updated_fields, previous_state=None):
        from extensions.authorization.models.user import User

        self.updated_fields: User = updated_fields
        self.previous_state: User = previous_state
