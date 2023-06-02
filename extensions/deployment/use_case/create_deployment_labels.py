from extensions.deployment.exceptions import DuplicateLabel, MaxDeploymentLabelsCreated
from extensions.deployment.models.deployment import Label
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import CreateLabelsRequestObject
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class CreateDeploymentLabelsUseCase(UseCase):
    @autoparams()
    def __init__(self, repository: DeploymentRepository):
        self._repository = repository

    def process_request(self, request_object: CreateLabelsRequestObject):
        labels = self.retrieve_deployment_labels(
            deployment_id=request_object.deploymentId
        )
        self._check_label_exceeds_maximum_number(
            labels=labels, texts=request_object.texts
        )
        if labels and self._check_labels_for_existing_text(
            request_object.texts, labels
        ):
            raise DuplicateLabel
        new_label_ids = self.create_deployment_label(request_object)
        return Response(value=new_label_ids)

    def create_deployment_label(self, request_object: CreateLabelsRequestObject):

        labels = [
            Label.from_dict(
                {
                    Label.TEXT: text,
                    Label.AUTHOR_ID: request_object.submitterId,
                }
            )
            for text in request_object.texts
        ]
        return self._repository.create_deployment_labels(
            deployment_id=request_object.deploymentId, labels=labels
        )

    def retrieve_deployment_labels(self, deployment_id: str) -> list[Label]:
        deployment = self._repository.retrieve_deployment(deployment_id=deployment_id)
        if not deployment.features.labels:
            raise ObjectDoesNotExist(message="Label feature is not enabled")
        return deployment.labels

    @staticmethod
    def _check_labels_for_existing_text(label_texts: list[str], labels: list[Label]):
        exists = next((label for label in labels if label.text in label_texts), None)
        return bool(exists)

    @staticmethod
    def _check_label_exceeds_maximum_number(
        labels: list[Label], texts: list[str]
    ) -> bool:
        number_of_labels = len(labels) if labels else 0
        if number_of_labels >= 100:
            raise MaxDeploymentLabelsCreated

        number_of_texts = len(texts)
        label_diff = number_of_labels + number_of_texts - 100
        if label_diff > 0:
            raise MaxDeploymentLabelsCreated(
                f"Adding {number_of_texts} labels to Deployment would exceed max by {label_diff}"
            )
