import abc
from abc import ABC

from sdk.auth.model.auth_user import AuthUser, AuthKey
from sdk.auth.model.session import DeviceSession, DeviceSessionV1


class AuthRepository(ABC):
    session = None

    @abc.abstractmethod
    def create_user(self, auth_user: AuthUser, **kwargs) -> str:
        """
        :param auth_user:
        :param kwargs: i.e. session info
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_user(
        self, phone_number: str = None, email: str = None, uid: str = None, **kwargs
    ) -> AuthUser:
        raise NotImplementedError

    @abc.abstractmethod
    def register_device_session(self, session: DeviceSessionV1) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_device_sessions_by_user_id(
        self, user_id: str, only_enabled: bool = True
    ) -> list[DeviceSession]:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_device_session(
        self,
        user_id: str,
        device_agent: str = None,
        refresh_token: str = None,
        check_is_active: bool = False,
    ) -> DeviceSession:
        raise NotImplementedError

    @abc.abstractmethod
    def update_device_session(self, session: DeviceSession):
        raise NotImplementedError

    @abc.abstractmethod
    def update_device_session_v1(
        self, session: DeviceSession, refresh_token: str = None
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def sign_out_device_session(self, session: DeviceSession) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def sign_out_device_session_v1(self, session: DeviceSessionV1) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def commit_transactions(self):
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_transactions(self):
        raise NotImplementedError

    @abc.abstractmethod
    def validate_password(
        self, password: str, email: str = None, uid: str = None
    ) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def confirm_email(self, email: str, uid: str = None):
        raise NotImplementedError

    @abc.abstractmethod
    def confirm_phone_number(self, phone_number: str):
        raise NotImplementedError

    @abc.abstractmethod
    def change_password(self, password: str, email: str, previous_passwords: list[str]):
        raise NotImplementedError

    @abc.abstractmethod
    def set_auth_attributes(
        self,
        uid: str,
        password: str = None,
        email: str = None,
        mfa_identifiers: list = None,
        mfa_enabled: bool = None,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def check_phone_number_exists(self, phone_number: str):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user(self, user_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def create_auth_keys(
        self,
        user_id: str,
        auth_key: str,
        auth_identifier: str,
        auth_type: AuthKey.AuthType,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_auth_key(self, user_id: str, auth_identifier: str):
        raise NotImplementedError

    @abc.abstractmethod
    def validate_device_token(self, device_token: str, user_id: str):
        raise NotImplementedError


class AuthHook(ABC):
    @abc.abstractmethod
    def on_create_user(self):
        raise NotImplementedError
