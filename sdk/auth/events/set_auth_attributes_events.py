from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class PostSetAuthAttributesEvent(BaseEvent, Convertible):
    def __init__(
        self,
        user_id: str,
        password: str = None,
        email: str = None,
        mfa_identifiers: list = None,
        mfa_enabled: bool = None,
        old_password: str = None,
        language: str = None,
        mfa_phone_number_updated: bool = False,
        mfa_device_token_updated: bool = False,
    ):
        self.user_id = user_id
        self.password = password
        self.email = email
        self.mfa_identifiers = mfa_identifiers
        self.mfa_enabled = mfa_enabled
        self.old_password = old_password
        self.language = language
        self.mfa_phone_number_updated = mfa_phone_number_updated
        self.mfa_device_token_updated = mfa_device_token_updated


class PreSetAuthAttributesEvent(BaseEvent, Convertible):
    def __init__(
        self,
        user_id=None,
        password: str = None,
        email: str = None,
        mfa_identifiers: list = None,
        mfa_enabled: bool = None,
    ):
        self.user_id = user_id
        self.password = password
        self.email = email
        self.mfa_identifiers = mfa_identifiers
        self.mfa_enabled = mfa_enabled


class PreRequestPasswordResetEvent(BaseEvent, Convertible):
    def __init__(
        self,
        user_id=None,
        client_id=None,
        project_id=None,
    ):
        self.user_id = user_id
        self.client_id = client_id
        self.project_id = project_id
