from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.inject import autoparams


class UpdateUserProfileUseCase(BaseAuthorizationUseCase):
    @autoparams("repo")
    def __init__(self, repo: AuthorizationRepository, deployment_id: str):
        super(UpdateUserProfileUseCase, self).__init__(repo)
        self.service = AuthorizationService()
        self.deployment_id = deployment_id

    def execute(self, request_object):
        if request_object.preferredUnits:
            self.service.validate_user_preferred_units(request_object.preferredUnits)
        self.request_object = request_object
        return super(UpdateUserProfileUseCase, self).execute(request_object)

    def process_request(self, request_object):
        self.service.update_covid_risk_score(request_object, self.deployment_id)
        updated_id = self.service.update_user_profile(request_object)

        return Response(value=updated_id)
