from abc import ABC, abstractmethod
from typing import Optional, Union

from extensions.authorization.models.role.role import Role
from extensions.common.sort import SortField
from extensions.deployment.models.status import Status
from extensions.organization.models.organization import (
    Organization,
    OrganizationWithDeploymentInfo,
)


class OrganizationRepository(ABC):
    @abstractmethod
    def create_organization(self, organization: Organization) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organization(self, organization_id: str) -> Organization:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organization_with_deployment_data(
        self, organization_id: str
    ) -> OrganizationWithDeploymentInfo:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organizations(
        self,
        skip: int = None,
        limit: int = None,
        name_contains: Optional[str] = None,
        sort_fields: Optional[list[SortField]] = None,
        ids: list[str] = None,
        deployment_ids: list[str] = None,
        search_criteria: Optional[str] = None,
        status: list[Status] = None,
    ) -> tuple[list[Organization], int]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organization_by_deployment_id(
        self, deployment_id: str
    ) -> Union[Organization, None]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organization_ids(self, deployment_ids: list[str] = None):
        raise NotImplementedError

    @abstractmethod
    def update_organization(self, organization: Organization) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_organization(self, organization_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def unlink_deployment(self, organization_id: str, deployment_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def link_deployment(self, organization_id: str, deployment_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def link_deployments(self, organization_id: str, deployment_ids: list[str]) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_or_update_roles(
        self, organization_id: str, roles: list[Role]
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def unlink_deployments(self, organization_id: str, deployment_ids: list[str]):
        raise NotImplementedError

    @abstractmethod
    def retrieve_organizations_by_ids(
        self, organization_ids: list[str]
    ) -> list[Organization]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_organization_by_name(self, organization_name: str) -> Organization:
        raise NotImplementedError
