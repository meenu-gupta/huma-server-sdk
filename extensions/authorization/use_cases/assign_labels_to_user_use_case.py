from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    AssignLabelsToUserRequestObject,
)
from extensions.authorization.use_cases.base_user_label_use_case import (
    BaseUserLabelsUseCase,
)
from extensions.deployment.models.deployment import Label
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.response_object import Response
from sdk.common.utils import inject


class AssignLabelsToUserUseCase(BaseUserLabelsUseCase):
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

    def process_request(self, request_object: AssignLabelsToUserRequestObject):
        deployment_labels = self.retrieve_deployment_labels(
            deployment_id=request_object.deploymentId
        )
        user_id = self.assign_labels_to_user(
            user_id=request_object.userId,
            label_ids=request_object.labelIds,
            assignee_id=request_object.assignedBy,
            deployment_labels=deployment_labels,
        )
        return Response(value={"id": user_id})

    def assign_labels_to_user(
        self,
        user_id: str,
        label_ids: list[str],
        assignee_id: str,
        deployment_labels: list[Label],
    ):
        deployment_labels_ids = []
        user_labels = []
        for label in deployment_labels:
            deployment_labels_ids.append(label.id)
            if label.id in label_ids:
                user_labels.append(label)

        unsupported_ids = [
            label_id for label_id in label_ids if label_id not in deployment_labels_ids
        ]
        if unsupported_ids:
            raise ObjectDoesNotExist(
                message=f"labels with ids {unsupported_ids} do not exist"
            )

        user_id = self._repo.assign_labels_to_user(user_id, user_labels, assignee_id)
        self._post_assign_labels(
            user_ids=[user_id], labels=user_labels, assignee_id=assignee_id
        )

        return user_id
