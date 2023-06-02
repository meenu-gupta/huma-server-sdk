from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.router.user_profile_request import (
    AssignManagerRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AssignManagerUseCase(BaseAuthorizationUseCase):
    def process_request(self, request_object: AssignManagerRequestObject):
        auth_user = self.get_auth_user()
        self.validate_manager_ids(
            deployment_id=auth_user.deployment_id(),
            manager_ids=request_object.managerIds,
        )
        inserted_id = self.auth_repo.assign_managers_and_create_log(
            manager_assigment=request_object
        )
        return Response({"id": inserted_id})

    def get_auth_user(self):
        user = AuthorizationService().retrieve_user_profile(self.request_object.userId)
        return AuthorizedUser(user)

    def validate_manager_ids(self, deployment_id: str, manager_ids: list[str]):
        manager_ids = set(manager_ids)
        if not manager_ids:
            return
        managers = AuthorizationService().retrieve_user_profiles_by_ids(manager_ids)

        for auth_manager in map(lambda x: AuthorizedUser(x, deployment_id), managers):
            if not auth_manager.is_manager():
                role = auth_manager.get_role()
                msg = f"Expected role [Manager], got [{role and role.id}]."
                raise ConvertibleClassValidationError(msg)
            if auth_manager.deployment_id() != deployment_id:
                msg = f"Manager #{auth_manager.id} does not exist in deployment #{deployment_id}."
                raise ConvertibleClassValidationError(msg)
