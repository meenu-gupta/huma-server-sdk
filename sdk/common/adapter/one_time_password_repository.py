import abc
from dataclasses import field
from datetime import datetime

from sdk import convertibleclass
from sdk.common.utils.convertible import required_field


@convertibleclass
class OneTimePasswordConfig:
    rateLimit: int = field(default=8)


@convertibleclass
class OneTimePassword:
    DEFAULT_TYPE = "Verification"

    IDENTIFIER = "identifier"
    PASSWORD = "password"
    TYPE = "type"
    NUMBER_OF_TRY = "numberOfTry"
    CREATED_AT = "createdAt"

    identifier: str = required_field()
    password: str = required_field()
    type: str = field(default=DEFAULT_TYPE)
    numberOfTry: int = field(default=1)
    createdAt: str = field(default_factory=datetime.utcnow)


class OneTimePasswordRepository(abc.ABC):
    @abc.abstractmethod
    def create_otp(self, otp: OneTimePassword):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_otp(self, identifier: str, code_type: str) -> OneTimePassword:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_or_get_password(
        self,
        identifier: str,
        password_length: int = 6,
        include_characters: bool = False,
    ) -> str:
        """
        :return: the return should not be None if it's successful
        """
        raise NotImplementedError

    @abc.abstractmethod
    def verify_password(
        self, identifier: str, password: str, code_type: str = None, delete: bool = True
    ) -> bool:
        """
        :return: return false if it's not valid
        """
        raise NotImplementedError

    def delete_otp(self, identifier: str, code_type: str, code: str = None):
        raise NotImplementedError
