import abc
from abc import ABC


class SmsAdapter(ABC):
    @abc.abstractmethod
    def send_sms(
        self, phone_number: str, text: str, phone_number_source: str
    ) -> object:
        """
        :param phone_number:
        :param text:
        :param phone_number_source
        :return: the return should not be None if it's successful
        """
