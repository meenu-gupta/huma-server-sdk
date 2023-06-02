from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import RetrieveLabelsRequestObject
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveDeploymentLabelsUseCase(UseCase):
    @autoparams()
    def __init__(
        self, repository: DeploymentRepository, user_repository: AuthorizationRepository
    ):
        self._repository = repository
        self.user_repository = user_repository

    def process_request(self, request_object: RetrieveLabelsRequestObject):
        deployment = self._repository.retrieve_deployment(
            deployment_id=request_object.deploymentId
        )
        if not deployment.features.labels:
            raise ObjectDoesNotExist(message="Label feature is not enabled")

        deployment_labels = deployment.labels
        if not deployment_labels:
            return Response(value=[])

        users_per_label_dict = self.user_repository.get_users_per_label_count(
            deployment_id=request_object.deploymentId
        )
        deployment_labels_dict = list()
        for label in deployment_labels:
            label_dict = label.to_dict()
            if label.id in users_per_label_dict:
                label_dict["count"] = users_per_label_dict[label.id]
            else:
                label_dict["count"] = 0
            deployment_labels_dict.append(label_dict)

        return Response(value=deployment_labels_dict)
