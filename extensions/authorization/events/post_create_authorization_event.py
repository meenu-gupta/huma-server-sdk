from extensions.authorization.events.base_authorization_event import (
    BaseAuthorizationEvent,
)


class PostCreateAuthorizationEvent(BaseAuthorizationEvent):
    def __init__(self, **kwargs):
        super(PostCreateAuthorizationEvent, self).__init__(**kwargs)
        self.id = kwargs["id"]
        self.create_date_time = kwargs["create_date_time"]
