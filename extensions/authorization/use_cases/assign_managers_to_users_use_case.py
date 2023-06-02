from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.router.user_profile_request import (
    AssignManagersToUsersRequestObject,
)
from extensions.authorization.models.role.role import Role
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AssignManagersToUsersUseCase(BaseAuthorizationUseCase):
    def process_request(self, request_object: AssignManagersToUsersRequestObject):
        auth_user = self.get_auth_user()
        deployment_ids = auth_user.deployment_ids()
        if request_object.allUsers:
            user_ids = []
            for deployment_id in deployment_ids:
                deployment_user_ids = self.auth_repo.retrieve_user_ids_in_deployment(
                    deployment_id=deployment_id
                )
                user_ids.extend(deployment_user_ids)
        else:
            user_ids = request_object.userIds
            self.validate_user_ids(
                deployment_ids=deployment_ids,
                user_ids=user_ids,
                role=Role.UserType.USER,
            )
        if not user_ids:
            return Response({"assignedUsers": 0})
        self.validate_user_ids(
            deployment_ids=deployment_ids,
            user_ids=request_object.managerIds,
            role=Role.UserType.MANAGER,
        )
        self.auth_repo.assign_managers_to_users(
            manager_ids=request_object.managerIds,
            user_ids=user_ids,
            submitter_id=request_object.submitterId,
        )
        return Response({"assignedUsers": len(user_ids)})

    def get_auth_user(self):
        user = AuthorizationService().retrieve_simple_user_profile(
            self.request_object.submitterId
        )
        return AuthorizedUser(user)

    def validate_user_ids(
        self, deployment_ids: list[str], user_ids: list[str], role: str
    ):
        user_ids = set(user_ids)
        if not user_ids:
            return
        users = AuthorizationService().retrieve_simple_user_profiles_by_ids(user_ids)
        for auth_user in map(lambda x: AuthorizedUser(x), users):
            has_expected_role = (
                auth_user.is_manager()
                if role == Role.UserType.MANAGER
                else auth_user.is_user()
            )
            if not has_expected_role:
                actual_role = auth_user.get_role()
                msg = f"Expected role [{role}], got [{actual_role and actual_role.id}]."
                raise ConvertibleClassValidationError(msg)
            if not any(
                user_deployment_id in deployment_ids
                for user_deployment_id in auth_user.deployment_ids()
            ):
                msg = f"User #{auth_user.id} does not exist in deployments: {deployment_ids}."
                raise ConvertibleClassValidationError(msg)
