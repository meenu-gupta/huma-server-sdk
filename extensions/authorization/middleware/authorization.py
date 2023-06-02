from functools import cached_property
from typing import Optional

from flask import Request, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    UpdateUserProfileRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.exceptions.exceptions import (
    UserWithoutAnyRoleException,
    PermissionDenied,
)
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import is_all_items_equal
from sdk.common.utils.flask_request_utils import get_key_value_from_request
from sdk.common.utils.validators import incorrect_language_to_default


class AuthorizationMiddleware:
    DEPLOYMENT_ID_KEY = "deploymentId"
    DEPLOYMENT_VIEW_ARG_KEY = "deployment_id"
    DEPLOYMENT_HEADER_KEY = "x-deployment-id"

    ORGANIZATION_ID_KEY = "organizationId"
    ORGANIZATION_VIEW_ARG_KEY = "organization_id"
    ORGANIZATION_HEADER_KEY = "x-org-id"

    def __init__(self, request: Request):
        self.request = request

    def __call__(self, user_id):
        g.user = self._get_profile(user_id)
        if not g.user.roles:
            raise UserWithoutAnyRoleException

        self.get_language_from_headers_and_update_user_if_different()
        g.authz_user = self.get_authz_user(g.user)

        g.path_user = self.path_user
        if g.path_user:
            g.authz_path_user = self.get_authz_user(g.path_user)
        else:
            g.authz_path_user = None

    @staticmethod
    def _get_profile(user_id: str):
        return AuthorizationService().retrieve_simple_user_profile(user_id)

    @cached_property
    def deployment_id(self) -> Optional[str]:
        accessible_resources = self.accessible_resources("deployment")
        if not accessible_resources:
            return None

        if is_all_items_equal(accessible_resources):
            return accessible_resources[0]
        raise PermissionDenied("Access of different resources")

    @cached_property
    def organization_id(self) -> Optional[str]:
        accessible_resources = self.accessible_resources("organization")
        if accessible_resources:
            if is_all_items_equal(accessible_resources):
                return accessible_resources[0]
            raise PermissionDenied("Access of different resources")

        if not self.deployment_id:
            return None

        repo = inject.instance(OrganizationRepository)
        org_ids = repo.retrieve_organization_ids(deployment_ids=[self.deployment_id])
        return next(iter(org_ids), None)

    def get_authz_user(self, user: User) -> AuthorizedUser:
        authz_user = AuthorizedUser(user, self.deployment_id, self.organization_id)
        if not authz_user.get_role():
            raise PermissionDenied
        return authz_user

    def get_language_from_headers_and_update_user_if_different(self):
        new_language = self.request.headers.get("x-hu-locale", None)
        if not new_language:
            return

        new_language = incorrect_language_to_default(new_language)
        if new_language == g.user.language:
            return

        user = UpdateUserProfileRequestObject(
            id=g.user.id, language=new_language, previousState=g.user
        )
        AuthorizationService().update_user_profile(user)
        g.user.language = new_language

    @cached_property
    def path_user(self) -> Optional[User]:
        view_args = self.request.view_args or {}
        path_user_id = view_args.get("user_id") or view_args.get("manager_id")
        if not path_user_id:
            path_user_id = self._path_user_id_from_filename()

        return self._get_profile(path_user_id) if path_user_id else None

    def _path_user_id_from_filename(self) -> Optional[str]:
        filename_key = "filename"
        resource: dict = self.request.form
        if self.request.method == "GET":
            resource = self.request.view_args

        try:
            filename = resource.get(filename_key)
            resource, resource_id, filename = filename.split("/", 2)
            return resource_id if resource == "user" else None
        except (AttributeError, ValueError):
            return None

    def accessible_resources(self, resource_type: str):
        if resource_type == "organization":
            resources = (
                self.request.headers.get(self.ORGANIZATION_HEADER_KEY),
                self.request.args.get(self.ORGANIZATION_ID_KEY),
                (self.request.view_args or {}).get(self.ORGANIZATION_VIEW_ARG_KEY),
                get_key_value_from_request(self.request, self.ORGANIZATION_ID_KEY),
            )
        elif resource_type == "deployment":
            resources = (
                self.request.headers.get(self.DEPLOYMENT_HEADER_KEY),
                self.request.args.get(self.DEPLOYMENT_ID_KEY),
                (self.request.view_args or {}).get(self.DEPLOYMENT_VIEW_ARG_KEY),
                get_key_value_from_request(self.request, self.DEPLOYMENT_ID_KEY),
            )
        else:
            raise NotImplementedError(f"Resource {resource_type} is not supported")

        return list(filter(None, resources))
