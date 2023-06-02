import abc
from abc import ABC


class AuditAdapter(ABC):
    @abc.abstractmethod
    def error(self, label: str, msg: str, *args, **kwargs):
        """
        :param label:
        :param msg:
        :return: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def info(self, label: str, msg: str, *args, **kwargs):
        """
        :param label:
        :param msg:
        :return: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def debug(self, label: str, msg: str, *args, **kwargs):
        """
        :param label:
        :param msg:
        :return: None
        """
        raise NotImplementedError
