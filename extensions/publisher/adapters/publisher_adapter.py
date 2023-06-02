import logging
from abc import abstractmethod

from extensions.publisher.models.publisher import Publisher

logger = logging.getLogger(__name__)

MODULE_ID = "module_id"
PRIMITIVES = "primitives"
DEPLOYMENT_ID = "deployment_id"
DEVICE_NAME = "device_name"
MODULE_CONFIG_ID = "module_config_id"


class PublisherAdapter:
    def __init__(
        self,
        publisher: Publisher,
    ):
        self._publisher = publisher
        self._headers = ""
        self._message = ""

    @abstractmethod
    def prepare_publisher_data(self, event: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def send_ping(self):
        raise NotImplementedError

    @abstractmethod
    def transform_publisher_data(self, event: dict):
        raise NotImplementedError

    @abstractmethod
    def send_publisher_data(self):
        raise NotImplementedError
