from sdk.common.adapter.event_bus_adapter import BaseEvent
from sdk.common.utils.convertible import Convertible


class BaseAuthEvent(BaseEvent, Convertible):
    SESSION = "session"
    CLIENT_ID = "client_id"
    TIMEZONE = "timezone"
    ID = "id"

    def __init__(
        self,
        method=None,
        display_name=None,
        client_id=None,
        project_id=None,
        email=None,
        phone_number=None,
        timezone=None,
        validation_data=None,
        user_attributes=None,
        hashed_password=None,
        password=None,
        email_verified=None,
        phone_number_verified=None,
        update_date_time=None,
        create_date_time=None,
        status=None,
        id=None,
        session=None,
        language=None,
        device_agent=None,
        password_update_date_time=None,
        password_create_date_time=None,
        mfa_identifiers=None,
        mfa_enabled=None,
        auth_keys=None,
        role_id=None,
        resource=None,
        user_type=None,
        **kwargs,
    ):
        if not (email or phone_number):
            raise Exception("One of [email, phone_number] must be present.")
        self.id = id
        self.method = method
        self.email = email
        self.phone_number = phone_number
        self.timezone = timezone
        self.display_name = display_name
        self.validation_data: dict = validation_data or {}
        self.user_attributes: dict = user_attributes or {}
        self.status = status
        self.hashed_password = hashed_password
        self.password = password
        self.email_verified = email_verified
        self.client_id = client_id
        self.project_id = project_id
        self.update_date_time = update_date_time
        self.create_date_time = create_date_time
        self.session = session
        self.language = language
        self.phone_number_verified = phone_number_verified
        self.device_agent = device_agent
        self.password_update_date_time = password_update_date_time
        self.password_create_date_time = password_create_date_time
        self.mfa_identifiers = mfa_identifiers
        self.mfa_enabled = mfa_enabled
        self.auth_key = auth_keys
        self.roleId = role_id
        self.resource = resource
        self.user_type = user_type
