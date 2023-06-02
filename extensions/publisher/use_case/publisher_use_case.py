from extensions.publisher.repository.publisher_repository import PublisherRepository
from extensions.publisher.router.publisher_requests import (
    CreatePublisherRequestObject,
    UpdatePublisherRequestObject,
    RetrievePublishersRequestObject,
    DeletePublisherRequestObject,
    RetrievePublisherRequestObject,
)
from extensions.publisher.router.publisher_responses import (
    RetrievePublishersResponseObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BasePublisherUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: PublisherRepository):
        self._repo = repo

    def process_request(self, request_object):
        raise NotImplementedError


class CreatePublisherUseCase(BasePublisherUseCase):
    def process_request(self, request_object: CreatePublisherRequestObject):
        publisher_id = self._repo.create_publisher(request_object)

        return Response(publisher_id)


class UpdatePublisherUseCase(BasePublisherUseCase):
    def process_request(self, request_object: UpdatePublisherRequestObject):
        publisher_id = self._repo.update_publisher(request_object)

        return Response(publisher_id)


class RetrievePublisherUseCase(BasePublisherUseCase):
    def process_request(self, request_object: RetrievePublisherRequestObject):
        publisher = self._repo.retrieve_publisher(request_object.publisherId)
        return Response(publisher)


class RetrievePublishersUseCase(BasePublisherUseCase):
    def process_request(self, request_object: RetrievePublishersRequestObject):
        publishers, total = self._repo.retrieve_publishers(
            skip=request_object.skip,
            limit=request_object.limit,
        )

        return RetrievePublishersResponseObject(
            items=[publisher.to_dict() for publisher in publishers],
            total=total,
            skip=request_object.skip,
            limit=request_object.limit,
        )


class DeletePublisherUseCase(BasePublisherUseCase):
    def process_request(self, request_object: DeletePublisherRequestObject):
        self._repo.delete_publisher(request_object.publisherId)
        return Response()
