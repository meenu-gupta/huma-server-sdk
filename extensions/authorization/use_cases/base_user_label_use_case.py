from extensions.authorization.events.post_assign_label_event import PostAssignLabelEvent
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.models.deployment import Label
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject


class BaseUserLabelsUseCase(UseCase):
    @inject.autoparams()
    def __init__(
        self,
        auth_repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        event_bus: EventBusAdapter,
    ):
        self._repo = auth_repo
        self._event_bus = event_bus
        self.deployment_repo = deployment_repo

    def process_request(self, request_object):
        raise NotImplementedError

    def retrieve_deployment_labels(self, deployment_id: str) -> list[Label]:
        deployment = self.deployment_repo.retrieve_deployment(
            deployment_id=deployment_id
        )
        if not deployment.features.labels:
            raise ObjectDoesNotExist(message="Label feature is not enabled")
        return deployment.labels

    def _post_assign_labels(self, **kwargs):
        self._event_bus.emit(PostAssignLabelEvent(**kwargs))
