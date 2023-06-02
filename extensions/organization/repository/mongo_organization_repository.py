from datetime import datetime
from typing import Optional

from bson import ObjectId
from pymongo.database import Database

from extensions.authorization.models.role.role import Role
from extensions.common.sort import SortField
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.status import Status
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.exceptions import (
    OrganizationDoesNotExist,
    DeploymentNotLinked,
)
from extensions.organization.models.organization import (
    Organization,
    OrganizationWithDeploymentInfo,
    DeploymentInfo,
)
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.utils import format_sort_fields
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import escape
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import id_as_obj_id, remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoOrganizationRepository(OrganizationRepository):
    """Repository to work with organization collection."""

    IGNORED_FIELDS = (
        Organization.CREATE_DATE_TIME,
        Organization.UPDATE_DATE_TIME,
    )
    ORGANIZATION_COLLECTION = "organization"

    @autoparams()
    def __init__(self, database: Database):
        self._config = inject.instance(PhoenixServerConfig)
        self._db = database

    def create_organization(self, organization: Organization) -> str:
        organization.createDateTime = organization.updateDateTime = datetime.utcnow()
        organization_dict = organization.to_dict(
            include_none=False, ignored_fields=self.IGNORED_FIELDS
        )

        result = self._db[self.ORGANIZATION_COLLECTION].insert_one(organization_dict)

        return str(result.inserted_id)

    @id_as_obj_id
    def retrieve_organization(self, organization_id: str) -> Organization:
        organization_dict = self._retrieve_organization_dict(organization_id)
        organization = Organization.from_dict(organization_dict)
        organization.id = str(organization_dict[Organization.ID_])

        return organization

    def _retrieve_organization_dict(self, organization_id: str) -> dict:
        result = self._db[self.ORGANIZATION_COLLECTION].find_one(
            {Organization.ID_: organization_id}
        )
        if result is None:
            raise OrganizationDoesNotExist

        return result

    def _retrieve_organization_deployment_data(
        self, deployment_ids: list[str]
    ) -> list[DeploymentInfo]:
        collection = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        query = {Deployment.ID_: {"$in": [ObjectId(i) for i in deployment_ids]}}

        deployments = self._db[collection].find(
            query,
            projection={Deployment.ID_: 1, Deployment.NAME: 1},
        )

        res = []
        for deployment in deployments:
            deployment[Deployment.ID] = str(deployment[Deployment.ID_])
            deployment = DeploymentInfo.from_dict(deployment)
            res.append(deployment)
        return res

    @id_as_obj_id
    def retrieve_organization_with_deployment_data(
        self, organization_id: str
    ) -> OrganizationWithDeploymentInfo:
        organization_dict = self._retrieve_organization_dict(organization_id)
        organization = OrganizationWithDeploymentInfo.from_dict(organization_dict)
        organization.id = str(organization_dict[Organization.ID_])

        if organization.deploymentIds:
            deployments = self._retrieve_organization_deployment_data(
                organization.deploymentIds
            )
            organization.deployments = deployments

        return organization

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

        formatted_sort = None
        status = [st.name for st in status] if status else None
        text_search = self._prepare_organization_text_search(
            search_criteria, name_contains
        )
        main_aggregation = []
        filter_options = {}

        if status:
            filter_options = {Organization.STATUS: status and {"$in": status}}

        if sort_fields:
            formatted_sort = format_sort_fields(
                sort_fields=sort_fields,
                valid_sort_fields=Organization.VALID_SORT_FIELDS,
            )

        if ids:
            ops = {Organization.ID_: {"$in": [ObjectId(id_) for id_ in ids]}}
            filter_options.update(ops)

        if deployment_ids:
            ops = {Organization.DEPLOYMENT_IDS: {"$elemMatch": {"$in": deployment_ids}}}
            filter_options.update(ops)

        if text_search:
            filter_options.update(text_search)

        if formatted_sort:
            main_aggregation.append({"$sort": dict(formatted_sort)})

        main_aggregation.append({"$skip": skip or 0})

        if limit:
            main_aggregation.append({"$limit": limit})

        aggregation = [
            {"$addFields": {"id": {"$toString": "$_id"}}},
            {"$match": remove_none_values(filter_options)},
            {
                "$facet": {
                    "results": main_aggregation,
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        result = self._db[self.ORGANIZATION_COLLECTION].aggregate(aggregation)
        result = next(result)
        organization_data = result["results"]
        organizations = [
            self.organization_from_document(doc) for doc in organization_data
        ]

        if not result["totalCount"]:
            return organizations, 0

        return organizations, result["totalCount"][0]["count"]

    @staticmethod
    def organization_from_document(doc: dict) -> Organization:
        organization = Organization.from_dict(doc, use_validator_field=False)
        organization.id = str(doc[Organization.ID_])
        return organization

    @staticmethod
    def _prepare_organization_text_search(
        search_criteria: Optional[str] = None, name_contains: Optional[str] = None
    ) -> Optional[dict]:

        if search_criteria:
            search = {"$regex": escape(search_criteria), "$options": "i"}
            return {"$or": [{Organization.ID: search}, {Organization.NAME: search}]}
        elif name_contains:
            return {
                Organization.NAME: {"$regex": escape(name_contains), "$options": "i"}
            }

    def retrieve_organization_by_deployment_id(
        self, deployment_id: str
    ) -> Optional[Organization]:
        filter = {Organization.DEPLOYMENT_IDS: deployment_id}
        result = self._db[self.ORGANIZATION_COLLECTION].find_one(filter)

        if result is None:
            return None

        organization = Organization.from_dict(result)
        organization.id = str(result[Organization.ID_])

        return organization

    def retrieve_organization_ids(self, deployment_ids: list[str] = None) -> list[str]:
        filter_options = {}
        if deployment_ids:
            filter_options.update(
                {Organization.DEPLOYMENT_IDS: {"$elemMatch": {"$in": deployment_ids}}}
            )
        result = self._db[self.ORGANIZATION_COLLECTION].find(filter_options, {"_id": 1})
        return [str(item[Organization.ID_]) for item in result]

    def update_organization(self, organization: Organization) -> str:
        organization_dict = organization.to_dict(include_none=False)
        organization_dict[Organization.UPDATE_DATE_TIME] = datetime.utcnow()
        organization_id = ObjectId(organization_dict.pop("id"))

        updated_result = self._db[self.ORGANIZATION_COLLECTION].find_one_and_update(
            {Organization.ID_: organization_id},
            {
                "$set": organization_dict,
            },
        )

        if not updated_result:
            raise OrganizationDoesNotExist

        return organization.id

    @id_as_obj_id
    def delete_organization(self, organization_id: str) -> None:
        result = self._db[self.ORGANIZATION_COLLECTION].find_one_and_delete(
            {Organization.ID_: organization_id}
        )
        if result is None:
            raise OrganizationDoesNotExist

    @id_as_obj_id
    def unlink_deployment(self, organization_id: str, deployment_id: str):
        filter_query = {Organization.ID_: organization_id}
        update_query = {"$pull": {Organization.DEPLOYMENT_IDS: str(deployment_id)}}

        result = self._db[self.ORGANIZATION_COLLECTION].update_one(
            filter_query, update_query
        )
        self._verify_unlink_deployment_result(result)

    @id_as_obj_id
    def unlink_deployments(self, organization_id: str, deployment_ids: list[str]):
        filter_query = {Organization.ID_: organization_id}
        update_query = {"$pull": {Organization.DEPLOYMENT_IDS: {"$in": deployment_ids}}}

        result = self._db[self.ORGANIZATION_COLLECTION].update_one(
            filter_query, update_query
        )
        self._verify_unlink_deployment_result(result)

    @staticmethod
    def _verify_unlink_deployment_result(result):
        if not result.matched_count:
            raise OrganizationDoesNotExist

        if not result.modified_count:
            raise DeploymentNotLinked

    @id_as_obj_id
    def link_deployment(self, organization_id: str, deployment_id: str) -> str:
        filter_query = {Organization.ID_: organization_id}
        update_query = {"$push": {Organization.DEPLOYMENT_IDS: str(deployment_id)}}

        result = self._db[self.ORGANIZATION_COLLECTION].update_one(
            filter_query, update_query
        )

        if not result.modified_count:
            raise OrganizationDoesNotExist

        return str(organization_id)

    @id_as_obj_id
    def link_deployments(self, organization_id: str, deployment_ids: list[str]) -> str:
        filter_query = {Organization.ID_: organization_id}
        update_query = {
            "$addToSet": {Organization.DEPLOYMENT_IDS: {"$each": deployment_ids}}
        }

        result = self._db[self.ORGANIZATION_COLLECTION].update_one(
            filter_query, update_query
        )
        if not result.matched_count:
            raise OrganizationDoesNotExist

        return str(organization_id)

    @id_as_obj_id
    def create_or_update_roles(
        self, organization_id: str, roles: list[Role]
    ) -> list[str]:
        role_dicts = []

        for role in roles:
            role.id = role.id or str(ObjectId())
            role_dict = role.to_dict(include_none=False)
            role_dict[Role.ID] = ObjectId(role.id)
            role_dicts.append(role_dict)

        filter_query = {Organization.ID_: organization_id}
        update_query = {"$set": {Organization.ROLES: role_dicts}}
        result = self._db[self.ORGANIZATION_COLLECTION].update_one(
            filter_query, update_query
        )

        if not result.matched_count:
            raise OrganizationDoesNotExist

        return [role.id for role in roles]

    def retrieve_organization_by_name(self, organization_name: str) -> Organization:
        result = self._db[self.ORGANIZATION_COLLECTION].find_one(
            {
                Organization.NAME: {
                    "$regex": f"^{escape(organization_name)}$",
                    "$options": "i",
                }
            }
        )
        if not result:
            raise OrganizationDoesNotExist
        return self.organization_from_document(result)

    def retrieve_organizations_by_ids(
        self, organization_ids: list[str]
    ) -> list[Organization]:
        organization_ids = [
            ObjectId(id_) for id_ in organization_ids if ObjectId.is_valid(id_)
        ]
        result = self._db[self.ORGANIZATION_COLLECTION].find(
            {Organization.ID_: {"$in": organization_ids}}
        )

        return [self.organization_from_document(doc) for doc in result]
