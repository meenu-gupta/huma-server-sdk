import abc
from abc import ABC

from sdk.common.localization.utils import Language


class SmsVerificationAdapter(ABC):
    @abc.abstractmethod
    def send_verification_code(
        self,
        phone_number: str,
        channel: str = "sms",
        locale: str = Language.EN,
        sms_retriever_code: str = "",
    ) -> object:
        """
        :param phone_number:
        :param channel
        :param locale
        :param sms_retriever_code
        :return: the return should not be None if it's successful
        """
        raise NotImplementedError

    @abc.abstractmethod
    def verify_code(self, code: str, phone_number: str) -> bool:
        """
        :param code:
        :param phone_number:
        :return: return false if it's not valid
        """
        raise NotImplementedError
