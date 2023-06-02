from extensions.organization.events import PostDeleteOrganizationEvent
from extensions.organization.router import DeleteOrganizationRequestObject
from extensions.organization.use_case.base_organization_use_case import (
    BaseOrganizationUseCase,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import autoparams


class DeleteOrganizationUseCase(BaseOrganizationUseCase):
    request_object: DeleteOrganizationRequestObject

    def process_request(self, request_object):
        self.repo.delete_organization(organization_id=request_object.organizationId)
        self._post_delete()

    @autoparams("event_bus")
    def _post_delete(self, event_bus: EventBusAdapter):
        event = PostDeleteOrganizationEvent(
            self.request_object.organizationId,
            self.request_object.submitterId,
        )
        event_bus.emit(event)
