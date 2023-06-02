import logging
from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.authorization.models.role.role import CustomRolesExtension
from extensions.common.legal_documents import LegalDocument
from extensions.dashboard.models.dashboard import DashboardId
from extensions.deployment.models.status import Status
from sdk import meta, convertibleclass
from sdk.common.utils.convertible import default_field, required_field
from sdk.common.utils.validators import (
    validate_object_id,
    validate_entity_name,
    default_datetime_meta,
    validate_object_ids,
    validate_id,
)

logger = logging.getLogger(__name__)


class ViewType(Enum):
    DCT = "DCT"
    RPM = "RPM"


@convertibleclass
class Organization(CustomRolesExtension, LegalDocument):
    """Organization model for managing deployments"""

    ID = "id"
    ID_ = "_id"
    NAME = "name"
    DEPLOYMENT_ID = "deploymentId"
    DEPLOYMENT_IDS = "deploymentIds"
    ENROLLMENT_TARGET = "enrollmentTarget"
    STUDY_COMPLETION_TARGET = "studyCompletionTarget"
    STATUS = "status"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    VALID_SORT_FIELDS = [NAME]
    VIEW_TYPE = "viewType"
    TARGET_CONSENTED = "targetConsented"
    DASHBOARD_ID = "dashboardId"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    name: str = default_field(metadata=meta(validate_entity_name))
    status: Status = default_field()
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    enrollmentTarget: int = default_field()
    studyCompletionTarget: int = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    viewType: ViewType = default_field()
    targetConsented: int = default_field()
    dashboardId: DashboardId = default_field(
        metadata=meta(field_to_value=lambda x: x.value),
    )


class OrganizationAction(Enum):
    CreateOrganization = "CreateOrganization"
    UpdateOrganization = "UpdateOrganization"
    DeleteOrganization = "DeleteOrganization"

    LinkDeployment = "LinkDeployment"
    UnLinkDeployment = "UnLinkDeployment"

    CreateOrUpdateRoles = "CreateOrUpdateRoles"


@convertibleclass
class DeploymentInfo:
    ID = "id"
    NAME = "name"

    id: str = required_field(metadata=meta(validate_id, value_to_field=str))
    name: str = required_field(metadata=meta(validate_entity_name))


@convertibleclass
class OrganizationWithDeploymentInfo(Organization):
    DEPLOYMENTS = "deployments"

    deployments: list[DeploymentInfo] = default_field()
