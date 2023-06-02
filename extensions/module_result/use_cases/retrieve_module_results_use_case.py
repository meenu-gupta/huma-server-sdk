from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.event_bus.post_retrieve_primitive import (
    PostRetrievePrimitiveEvent,
)
from extensions.module_result.models.primitives import ECGHealthKit, Primitive
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.router.module_result_requests import (
    RetrieveModuleResultRequestObject,
)
from extensions.module_result.use_cases.search_module_results_response_object import (
    RetrieveModuleResultResponseObject,
    HealthKitResponseData,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


def process_ecg_primitive(primitive: Primitive):
    if type(primitive).__name__ == ECGHealthKit.__name__:
        primitive_data = primitive.to_dict(include_none=False)
        primitive = HealthKitResponseData.from_dict(
            primitive_data, use_validator_field=False
        )
    return primitive


class RetrieveModuleResultUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: ModuleResultRepository, event_bus: EventBusAdapter):
        self._repo = repo
        self._deployment_service = DeploymentService()
        self._event_bus = event_bus

    def process_request(self, request_object: RetrieveModuleResultRequestObject):
        primitive = self._repo.retrieve_primitive(
            request_object.userId,
            request_object.primitiveType,
            request_object.moduleResultId,
        )
        primitive = process_ecg_primitive(primitive)
        self.post_retrieve_event(primitive)
        return RetrieveModuleResultResponseObject(primitive)

    def post_retrieve_event(self, primitive: Primitive):
        event = PostRetrievePrimitiveEvent.from_primitive(primitive)
        self._event_bus.emit(event, raise_error=True)
