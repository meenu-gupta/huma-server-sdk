from abc import ABC, abstractmethod

from extensions.publisher.models.publisher import Publisher


class PublisherRepository(ABC):
    @abstractmethod
    def create_publisher(self, publisher: Publisher) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_publisher(self, publisher: Publisher) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_publishers(
        self,
        skip: int,
        limit: int,
    ) -> tuple[list[Publisher], int]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_publisher(self, publisher_id: str) -> Publisher:
        raise NotImplementedError

    @abstractmethod
    def delete_publisher(self, publisher_id: str):
        raise NotImplementedError
