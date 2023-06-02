from pymongo.client_session import ClientSession

from sdk.common.adapter.event_bus_adapter import BaseEvent


class DeleteUserEvent(BaseEvent):
    def __init__(self, session: ClientSession, user_id: str):
        self.session = session
        self.user_id = user_id
