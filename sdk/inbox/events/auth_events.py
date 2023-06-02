from sdk.common.adapter.event_bus_adapter import BaseEvent


class InboxAuthEvent(BaseEvent):
    pass


class InboxSearchAuthEvent(BaseEvent):
    pass


class InboxConfirmAuthEvent(BaseEvent):
    pass


class InboxSendAuthEvent(BaseEvent):
    """
    Inbox send_message router triggers this event and expects to have
    fullname in `g.user_full_name`.
    """

    pass


class PreCreateMessageEvent(BaseEvent):
    def __init__(self, submitter_id=None, text=None, custom=None, receiver_id=None):
        self.text = text
        self.custom = custom
        self.submitter_id = submitter_id
        self.receiver_id = receiver_id
