from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    GenerateMasterTranslationRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from sdk.common.localization.utils import Language
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class GenerateMasterTranslationUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
    ):
        self.deployment_repo = deployment_repo

    def process_request(self, request_object: GenerateMasterTranslationRequestObject):
        service = DeploymentService()
        deployment = service.retrieve_deployment(
            deployment_id=request_object.deploymentId
        )
        multi_language_deployment = (
            deployment.generate_deployment_multi_language_state()
        )

        self.deployment_repo.update_full_deployment(
            deployment=multi_language_deployment
        )

        return Response(multi_language_deployment.localizations[Language.EN])
