from enum import Enum
from functools import cached_property
from typing import Optional, Union

from extensions.authorization.helpers import (
    get_deployment_custom_role,
    get_organization_custom_role,
)
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.localization.utils import Language, Localization
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams


@autoparams("repo")
def _get_organization(organization_id, repo: OrganizationRepository) -> Organization:
    return repo.retrieve_organization(organization_id=organization_id)


@autoparams("repo")
def _get_users_by_ids(ids: list[str], repo: AuthorizationRepository) -> list:
    if not ids:
        return []

    return repo.retrieve_user_profiles_by_ids(ids=set(ids), role=RoleName.USER)


@autoparams("auth_repo")
def _get_proxy_users(
    user_id: str, deployment_id: str, auth_repo: AuthorizationRepository
) -> list[User]:
    proxy_users = auth_repo.retrieve_assigned_to_user_proxies(user_id)
    return [
        user for user in proxy_users if AuthorizedUser(user, deployment_id).get_role()
    ]


class ProxyStatus(Enum):
    LINKED = "LINKED"
    UNLINK = "UNLINK"


class AuthorizedUser:
    """Proxy class for User model to simplify role access."""

    PROXY_DEPLOYMENT_ID = "deploymentId"
    PROXY_ID = "proxyId"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    ORGANIZATION_ID = "organizationId"
    USER_TYPE = "userType"
    ROLE = "roleId"
    ROLE_ASSIGNMENT = "roleAssignment"

    def __init__(
        self,
        user: User,
        deployment_id: str = None,
        organization_id: str = None,
        patient_id: str = None,
    ):
        self.user = user
        self._deployment_id = deployment_id
        self._organization_id = organization_id
        self._patient_id = patient_id
        self._role_assignment = self._init_role_assignment()
        self._role = self._init_role()

    def __str__(self):
        return (
            f"[{AuthorizedUser.__name__} {AuthorizedUser.DEPLOYMENT_ID}: {self._deployment_id}, "
            f"{AuthorizedUser.ORGANIZATION_ID}: {self._organization_id}, "
            f"{AuthorizedUser.ROLE}: {self._role.id}, "
            f"{AuthorizedUser.ROLE_ASSIGNMENT}: {self._role_assignment}]"
        )

    @property
    def role_assignment(self):
        return self._role_assignment

    def _init_role_assignment(self) -> Optional[RoleAssignment]:
        role_getters = [
            (self.deployment_role_assignment, "_deployment_id"),
            (self.organization_role_assignment, "_organization_id"),
            (self.proxy_role_assignment, "_patient_id"),
        ]
        if any((self._deployment_id, self._organization_id, self._patient_id)):
            role_getters.sort(key=lambda data: getattr(self, data[1], None) is None)

        for get_role, attr_name in role_getters:
            role_assignment = get_role(getattr(self, attr_name, None))
            if role_assignment:
                setattr(self, attr_name, role_assignment.resource_id())
                return role_assignment

        role_assignment = self._resource_role("organization", "*")
        if not role_assignment:
            return self._resource_role("deployment", "*")
        return role_assignment

    def _init_role(self) -> Optional[Role]:
        role_id = self._role_assignment.roleId if self._role_assignment else None
        role = inject.instance(DefaultRoles).get(role_id)
        if not role and self._deployment_id:
            role = get_deployment_custom_role(role_id, self._deployment_id)

        if not role and self._organization_id:
            role = get_organization_custom_role(role_id, self._organization_id)

        return role

    @property
    def id(self):
        return self.user.id

    def deployment_role_assignment(self, deployment_id=None):
        return self._resource_role("deployment", deployment_id)

    def deployment_id(self):
        if self._deployment_id:
            return self._deployment_id if self._role else None

        # TODO remove code block below when multiple roles are fully supported
        # finds FIRST deployment role in user roles list
        role = self.deployment_role_assignment()
        return role.resource_id() if role else None

    def organization_id(self):
        if self._organization_id:
            return self._organization_id if self._role else None
        role = self.organization_role_assignment()
        return role.resource_id() if role else None

    def deployment_ids(self, exclude_wildcard: bool = False):
        deployment_ids = []
        for role in self.user.roles:
            resource_id = role.resource_id()
            if role.is_org():
                if resource_id == "*":
                    continue
                ids = _get_organization(resource_id).deploymentIds or []
                deployment_ids.extend(ids)
                continue
            elif role.is_deployment():
                if resource_id != "*":
                    deployment_ids.append(resource_id)
                    continue
                if not exclude_wildcard:
                    deployment_ids = [resource_id]
                    break

        return deployment_ids

    @cached_property
    def deployment(self) -> Deployment:
        from extensions.deployment.service.deployment_service import DeploymentService

        return DeploymentService().retrieve_deployment_config(self)

    @cached_property
    def localization(self):
        user_language = self.get_language()
        deployment_localization = {}
        localization = inject.instance(Localization)
        default_localization = localization.get(user_language)
        if self.deployment_id():
            deployment_localization = self.deployment.get_localization(user_language)
        return {**default_localization, **deployment_localization}

    @cached_property
    def organization(self) -> Organization:
        return _get_organization(self.organization_id())

    def organization_ids(self) -> list[str]:
        return [
            role.resource_id()
            for role in self.user.roles
            if role.is_org() and role.resource_id() != "*"
        ]

    def proxy_participant_ids(self) -> list[str]:
        return [role.resource_id() for role in self.user.roles if role.is_proxy()]

    def get_role(self) -> Optional[Role]:
        return self._role

    def user_type(self) -> Optional[str]:
        role = self.get_role()
        if role:
            return role.userType
        return None

    def organization_role_assignment(
        self, organization_id: str = None
    ) -> Optional[RoleAssignment]:
        return self._resource_role("organization", organization_id)

    def proxy_role_assignment(self, patient_id: str = None) -> Optional[RoleAssignment]:
        return self._resource_role("user", patient_id)

    def is_proxy_for_user(self, user_id: str) -> bool:
        return bool(self._resource_role("user", user_id))

    def _resource_role(
        self, resource_key: str, resource_id: str
    ) -> Optional[RoleAssignment]:
        key = resource_key + (f"/{resource_id}" if resource_id else "")
        return self._get_role_by_resource(key)

    def get_consent(self) -> Consent:
        return self.deployment.consent

    def get_econsent(self) -> EConsent:
        return self.deployment.econsent

    def _get_role_by_resource(self, resource: str) -> Optional[RoleAssignment]:
        return next(
            filter(lambda r: resource in (r.resource or ""), self.user.roles or []),
            None,
        )

    def is_manager(self) -> bool:
        if self._role and self._role.userType:
            return self._role.userType == Role.UserType.MANAGER

        not_manager_types = (
            RoleName.SUPER_ADMIN,
            RoleName.HUMA_SUPPORT,
            RoleName.ACCOUNT_MANAGER,
            RoleName.ORGANIZATION_OWNER,
            RoleName.ORGANIZATION_EDITOR,
            RoleName.PROXY,
            RoleName.USER,
        )
        if self._role_assignment:
            return self._role_assignment.roleId not in not_manager_types

        return False

    def is_super_admin(self) -> bool:
        if self._role and self._role.userType:
            return self._role.userType == Role.UserType.SUPER_ADMIN
        if self._role_assignment:
            return self._role_assignment.roleId == RoleName.SUPER_ADMIN

        return False

    def is_user(self) -> bool:
        if self._role and self._role.userType:
            return self._role.userType == Role.UserType.USER
        if self._role_assignment:
            return self._role_assignment.roleId == RoleName.USER

        return False

    def is_proxy(self) -> bool:
        if self._role and self._role.userType:
            return self._role.userType == Role.UserType.PROXY
        if self._role_assignment:
            return self._role_assignment.roleId == RoleName.PROXY

        return False

    def get_language(self) -> str:
        if self.user.language:
            return self.user.language
        if self.deployment_id():
            return self.deployment.language
        return Language.EN

    def has_identifier_data_permission(self, user_id=None) -> bool:
        if self.user.id == user_id:
            return True

        if not self._role:
            return False

        return self._role.has([PolicyType.VIEW_PATIENT_IDENTIFIER])

    def get_assigned_proxies(self, to_dict=True) -> Optional[list[Union[User, dict]]]:
        """Returns proxy users assigned to current user"""
        if not self.is_user():
            return
        deployment_id = self.deployment_id()
        proxy_users = _get_proxy_users(self.id, deployment_id)
        if not to_dict:
            return proxy_users
        assigned_proxies = [
            {self.PROXY_DEPLOYMENT_ID: deployment_id, self.PROXY_ID: proxy.id}
            for proxy in proxy_users
        ]
        return assigned_proxies or None

    def get_assigned_participants(self) -> Optional[list[dict]]:
        """Returns participants whom current user is assigned as proxy"""
        if not self.is_proxy():
            return

        participants = self.proxy_participant_ids()
        deployment_id = self.deployment_id()

        users = _get_users_by_ids(participants)
        assigned_users = [
            {self.PROXY_DEPLOYMENT_ID: deployment_id, self.USER_ID: user.id}
            for user in users
        ]
        return assigned_users or None

    def get_proxy_link_status(self) -> Optional[ProxyStatus]:
        if not self.is_proxy():
            return
        participants = self.get_assigned_participants()
        for participant in participants or []:
            participant_deployment = participant[AuthorizedUser.PROXY_DEPLOYMENT_ID]
            if participant_deployment == self.deployment_id():
                return ProxyStatus.LINKED
        return ProxyStatus.UNLINK
