import abc
import datetime
from abc import ABC

from aenum import MultiValue, Enum


class TokenType(Enum):
    _init_ = "value string_value"
    _settings_ = MultiValue

    ACCESS = 0, "access"
    INVITATION = 1, "invitation"
    REFRESH = 2, "refresh"

    def __int__(self):
        return self.value


class TokenAdapter(ABC):
    @abc.abstractmethod
    def verify_token(
        self,
        token: str,
        request_type: str = TokenType.ACCESS.string_value,
        verify_user_claims=True,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def create_access_token(
        self,
        identity: str,
        user_claims: dict = None,
        expires_delta=datetime.timedelta(days=1),
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def create_refresh_token(
        self,
        identity: str,
        user_claims: dict = None,
        expires_delta: datetime.timedelta = None,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def create_confirmation_token(self, identity: str, user_claims: dict = None):
        raise NotImplementedError

    @abc.abstractmethod
    def verify_confirmation_token(self, token: str):
        raise NotImplementedError

    @abc.abstractmethod
    def verify_invitation_token(self, token: str, allow_expired=False):
        raise NotImplementedError

    @abc.abstractmethod
    def create_token(
        self,
        identity: str = None,
        token_type: str = None,
        user_claims: dict = None,
        expires_delta=False,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def reissue_refresh_token(self, token: str):
        raise NotImplementedError
