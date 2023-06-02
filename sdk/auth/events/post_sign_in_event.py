from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class PostSignInEvent(BaseEvent, Convertible):
    def __init__(
        self,
        user_id=None,
        refresh_token=None,
        device_agent=None,
        password=None,
        method=None,
        email=None,
        phone_number=None,
        client_id=None,
        project_id=None,
        confirmation_code=None,
        language=None,
        auth_stage=None,
    ):
        self.user_id = user_id
        self.password = password
        self.refresh_token = refresh_token
        self.device_agent = device_agent
        self.method = method
        self.email = email
        self.phone_number = phone_number
        self.confirmation_code = confirmation_code
        self.client_id = client_id
        self.project_id = project_id
        self.language = language
        self.auth_stage = auth_stage
