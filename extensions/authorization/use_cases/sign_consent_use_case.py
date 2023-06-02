import logging

from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.router.deployment_requests import SignConsentRequestObject
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.exceptions import ConsentDoesNotExist
from sdk.common.exceptions.exceptions import ConsentNotAgreedException
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__file__)


class SignConsentUseCase(UseCase):
    @autoparams()
    def __init__(self, consent_repo: ConsentRepository):
        self._consent_repo = consent_repo

    def execute(self, request_object: SignConsentRequestObject):
        service = DeploymentService(consent_repo=self._consent_repo)
        deployment = service.retrieve_deployment(request_object.deploymentId)
        consent = deployment.latest_consent
        if not consent or consent.id != request_object.consentId:
            raise ConsentDoesNotExist
        if consent.has_agreement_section() and not request_object.agreement:
            raise ConsentNotAgreedException

        return super(SignConsentUseCase, self).execute(request_object)

    def process_request(self, request_object: SignConsentRequestObject):
        response = self._consent_repo.create_consent_log(
            deployment_id=request_object.deploymentId, consent_log=request_object
        )
        return Response(value=response)
