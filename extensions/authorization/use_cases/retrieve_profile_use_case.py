from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.authorization.models.user_fields_converter import UserFieldsConverter
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    RetrieveUserProfileRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveProfileResponseObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from extensions.deployment.service.deployment_service import DeploymentService
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams


def _inject_proxy_data(user: User):
    authz_user = AuthorizedUser(user)
    user.assignedParticipants = authz_user.get_assigned_participants()
    user.assignedProxies = authz_user.get_assigned_proxies()
    user.proxyStatus = authz_user.get_proxy_link_status()


class RetrieveProfileUseCase(BaseAuthorizationUseCase):
    @autoparams()
    def __init__(self, repo: AuthorizationRepository):
        super().__init__(repo)
        self.service = AuthorizationService(repo)

    def process_request(
        self, request_object: RetrieveUserProfileRequestObject
    ) -> Response:

        user = self.service.retrieve_user_profile(
            user_id=request_object.userId, is_manager_request=request_object.isManager
        )

        deployment_id = request_object.deploymentId
        deployment = None
        if deployment_id not in [None, "", "*"]:
            deployment = DeploymentService().retrieve_deployment(
                deployment_id, raise_error=False
            )

        _inject_proxy_data(user)

        caller_language = request_object.callerLanguage
        if request_object.canViewIdentifierData:
            user_dict = UserFieldsConverter(user, deployment, caller_language).to_dict()
        else:
            user_dict = UserFieldsConverter(user, deployment, caller_language).to_dict(
                exclude_fields=user.identifiable_data_fields()
            )

        return RetrieveProfileResponseObject(user_dict)
