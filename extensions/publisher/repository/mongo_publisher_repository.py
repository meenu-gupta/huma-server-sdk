from mongoengine import NotUniqueError

from extensions.publisher.exceptions import DuplicatePublisherName
from extensions.publisher.models.mongo_publisher import MongoPublisher
from extensions.publisher.models.publisher import Publisher
from extensions.publisher.repository.publisher_repository import PublisherRepository
from sdk.common.exceptions.exceptions import ObjectDoesNotExist


class MongoPublisherRepository(PublisherRepository):
    """Repository to work with publisher collection."""

    def create_publisher(self, publisher: Publisher) -> str:
        try:
            mongo_publisher = MongoPublisher(**publisher.to_dict(include_none=False))
            document = mongo_publisher.save()
        except NotUniqueError:
            raise DuplicatePublisherName
        return str(document.id)

    def update_publisher(self, publisher: Publisher) -> str:
        old_publisher = MongoPublisher.objects(id=publisher.id).first()
        if not old_publisher:
            raise ObjectDoesNotExist(f"Publisher {publisher.id} does not exist")

        new_publisher = publisher.to_dict(include_none=False)

        try:
            old_publisher.update(**new_publisher)
        except NotUniqueError:
            raise DuplicatePublisherName
        return str(old_publisher.id)

    def retrieve_publishers(
        self,
        skip: int,
        limit: int,
    ) -> tuple[list[Publisher], int]:
        publisher_total_count = MongoPublisher.objects().count()

        if not publisher_total_count:
            return [], 0

        results = MongoPublisher.objects().skip(skip).limit(limit)
        publishers = [Publisher.from_dict(i.to_dict()) for i in results]

        return publishers, publisher_total_count

    def retrieve_publisher(self, publisher_id: str) -> Publisher:
        res = MongoPublisher.objects(id=publisher_id).first()
        if not res:
            raise ObjectDoesNotExist(f"Publisher {publisher_id} does not exist")

        return Publisher.from_dict(res.to_dict())

    def delete_publisher(self, publisher_id: str):
        res = MongoPublisher.objects(id=publisher_id).delete()

        if not res:
            raise ObjectDoesNotExist(f"Publisher {publisher_id} does not exist")
