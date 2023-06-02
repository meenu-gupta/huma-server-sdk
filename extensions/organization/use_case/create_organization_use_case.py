from extensions.organization.events import PostCreateOrganizationEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from extensions.organization.router.organization_requests import (
    CreateOrganizationRequestObject,
)
from sdk.common.utils.inject import autoparams
from sdk.common.usecase.response_object import Response


class CreateOrganizationUseCase(BaseOrganizationUseCase):
    def process_request(self, request_object: CreateOrganizationRequestObject):
        self._validate_no_organization_with_same_name(request_object.name)
        inserted_id = self.repo.create_organization(organization=request_object)

        request_object.id = inserted_id
        self._post_create()

        return Response(inserted_id)

    @autoparams("event_bus")
    def _post_create(self, event_bus: EventBusAdapter):
        event = PostCreateOrganizationEvent(
            self.request_object.id,
            self.request_object.submitterId,
            self.request_object.createDateTime,
        )
        event_bus.emit(event)
