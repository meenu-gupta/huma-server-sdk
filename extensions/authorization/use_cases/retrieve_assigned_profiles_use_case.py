from extensions.authorization.router.user_profile_request import (
    RetrieveAssignedProfilesRequestObject,
)
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from sdk.common.usecase.response_object import Response


class RetrieveAssignedProfilesUseCase(BaseAuthorizationUseCase):
    def process_request(self, request_object: RetrieveAssignedProfilesRequestObject):
        profiles = self.auth_repo.retrieve_profiles_with_assigned_manager(
            request_object.managerId
        )
        self._inject_assigned_managers_ids_to_users(profiles)
        return Response(profiles)
