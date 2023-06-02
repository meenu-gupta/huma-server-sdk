from extensions.authorization.router.user_profile_request import (
    RemoveRolesRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.utils.common_functions_utils import find
from .base_authorization_use_case import BaseAuthorizationUseCase
from ..models.user import User, RoleAssignment
from ...exceptions import RoleDoesNotExistException


class RemoveRolesUseCase(BaseAuthorizationUseCase):
    def process_request(self, request_object: RemoveRolesRequestObject):
        user = self.auth_repo.retrieve_simple_user_profile(
            user_id=request_object.userId
        )

        self._check_roles_exist(user.roles)
        roles = user.roles[:] if user.roles else []
        for role in request_object.roles:
            for user_role in roles:
                if role == user_role:
                    roles.remove(role)

        self._update_user_roles(user.id, roles)
        return Response(user.id)

    def _check_roles_exist(self, roles: list[RoleAssignment]):
        for role in self.request_object.roles:
            if not find(lambda r: r == role, roles):
                raise RoleDoesNotExistException(role.roleId)

    def _update_user_roles(self, user_id: str, roles) -> str:
        body = {User.ID: user_id, User.ROLES: roles}
        req_obj = User.from_dict(body, ignored_fields=(User.ROLES,))
        return self.auth_repo.update_user_profile(req_obj)
