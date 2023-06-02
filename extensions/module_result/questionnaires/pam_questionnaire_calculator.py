import logging

from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.config.pam_integration_client_config import (
    PAMIntegrationClientConfig,
)
from extensions.module_result.models.primitives import (
    Questionnaire,
    QuestionnaireAppResultValue,
    QuestionnaireAppResult,
)
from extensions.module_result.pam.pam_integration_client import PAMIntegrationClient
from sdk.common.utils import inject
from sdk.common.utils.encryption_utils import decrypt
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server
from .questionnaire_calculator import QuestionnaireCalculator

logger = logging.getLogger(__file__)


def get_pam_config(
    deployment: Deployment, server_config: Server
) -> PAMIntegrationClientConfig:
    pam_integration = server_config.moduleResult.pamIntegration

    if (
        deployment.integration
        and deployment.integration.pamConfig
        and deployment.integration.pamConfig.clientExtID
        and len(deployment.integration.pamConfig.clientExtID) > 0
        and server_config.deployment
        and server_config.deployment.encryptionSecret
    ):
        try:
            pam_config = deployment.integration.pamConfig
            pam_integration_config = PAMIntegrationClientConfig()
            pam_integration_config.clientExtID = pam_config.clientExtID
            pam_integration_config.enrollUserURI = pam_config.enrollUserURI
            pam_integration_config.subgroupExtID = pam_config.subgroupExtID
            pam_integration_config.submitSurveyURI = pam_config.submitSurveyURI
            pam_integration_config.clientPassKey = decrypt(
                message=pam_config.clientPassKeyEncrypted,
                secret=server_config.deployment.encryptionSecret,
            )
            pam_integration = pam_integration_config
        except BaseException as e:
            logger.warning(
                f"Error on creating pam configuration from deployment config: {str(e)}"
            )

    return pam_integration


class PAMQuestionnaireCalculator(QuestionnaireCalculator):
    def calculate(self, primitive: Questionnaire, module_config: ModuleConfig):
        from extensions.deployment.service.deployment_service import DeploymentService

        deployment = DeploymentService().retrieve_deployment(primitive.deploymentId)
        server_config = inject.instance(PhoenixServerConfig).server

        pam_integration = get_pam_config(deployment, server_config)

        logger.debug(
            f"Client ID {pam_integration.clientExtID} used for Deployment ID {deployment.id}"
        )

        pam_client: PAMIntegrationClient = inject.instance("pamIntegrationClient")
        authz_service = inject.instance(AuthorizationService)
        user = authz_service.retrieve_user_profile(user_id=primitive.userId)

        if not (third_party_identifier := user.pamThirdPartyIdentifier):
            third_party_identifier = pam_client.enroll_user(email=user.email)
            updated_user = UpdateUserProfileRequestObject(
                id=user.id,
                pamThirdPartyIdentifier=third_party_identifier,
                previousState=user,
            )
            user_id = authz_service.update_user_profile(user=updated_user)
            logger.info(
                f"Updated pamThirdPartyIdentifier {third_party_identifier} to user {user_id}"
            )

        score, level = pam_client.submit_survey(
            primitive=primitive,
            third_party_identifier=third_party_identifier,
        )

        app_result = QuestionnaireAppResult(
            appType=QuestionnaireAppResult.QuestionnaireAppResultType.GRADED_RESULT,
            values=[
                QuestionnaireAppResultValue(
                    label="PAMSCORE",
                    valueType=QuestionnaireAppResultValue.QuestionnaireAppResultValueType.VALUE_FLOAT,
                    valueFloat=score,
                ),
                QuestionnaireAppResultValue(
                    label="PAMRESULTLEVEL",
                    valueType=QuestionnaireAppResultValue.QuestionnaireAppResultValueType.VALUE_FLOAT,
                    valueFloat=level,
                ),
            ],
        )
        primitive.appResult = app_result
        primitive.value = score
        logger.info(f"PAM questionnaire result: {app_result} retrieved")
