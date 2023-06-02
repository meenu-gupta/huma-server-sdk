from extensions.deployment.exceptions import DuplicateLabel
from extensions.deployment.models.deployment import Label
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import UpdateLabelRequestObject
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class UpdateDeploymentLabelUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: UpdateLabelRequestObject):
        labels = self._repository.retrieve_deployment_labels(
            deployment_id=request_object.deploymentId
        )
        if labels and self._check_labels_for_existing_text(request_object.text, labels):
            raise DuplicateLabel
        label = Label.from_dict(
            {
                Label.ID: request_object.labelId,
                Label.TEXT: request_object.text,
                Label.UPDATED_BY: request_object.submitterId,
            }
        )
        deployment_id = self._repository.update_deployment_labels(
            deployment_id=request_object.deploymentId,
            labels=labels,
            updated_label=label,
        )
        return Response(value={"id": deployment_id})

    @staticmethod
    def _check_labels_for_existing_text(label_text, labels: list[Label]):
        exists = next((label for label in labels if label.text == label_text), None)
        return bool(exists)
