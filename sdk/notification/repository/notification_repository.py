import abc
from abc import ABC

from sdk.notification.model.device import Device


class NotificationRepository(ABC):
    @abc.abstractmethod
    def register_device(self, device: Device) -> str:
        """
        @param device: user's device object
        @return: insert or update user device
        """
        raise NotImplementedError

    @abc.abstractmethod
    def unregister_device(
        self, user_id: str, device_push_id: str = None, voip_device_push_id: str = None
    ):
        """
        @param user_id: user id
        @param device_push_id: device push id
        @return: deleted device id
        """
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_devices(self, user_id: str) -> list[Device]:
        """
        @param user_id: id of a user
        @return: list of user devices or empty list if not found
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_device(self, device_push_id: str) -> None:
        """
        @param device_push_id
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_devices(self, ids: list[str]) -> None:
        """
        @param ids - ids of devices to delete
        """
        raise NotImplementedError
