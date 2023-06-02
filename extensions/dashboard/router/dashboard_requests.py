from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.dashboard.models.dashboard import DashboardId, DashboardResourceType
from extensions.dashboard.models.gadget import GadgetId
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException
from sdk.common.utils.convertible import (
    meta,
    convertibleclass,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
)


@convertibleclass
class BaseDashboardRequestObject:
    RESOURCE_TYPE = "resourceType"
    RESOURCE_ID = "resourceId"
    SUBMITTER = "submitter"

    resourceType: DashboardResourceType = required_field()
    resourceId: str = required_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    submitter: AuthorizedUser = required_field()

    def check_permissions(self):
        if self.resourceType == DashboardResourceType.ORGANIZATION:
            if self.resourceId not in self.submitter.organization_ids():
                raise PermissionDenied
        elif self.resourceType == DashboardResourceType.DEPLOYMENT:
            self._check_deployment_dashboard_permission()
        else:
            raise InvalidRequestException

    def _check_deployment_dashboard_permission(self):
        raise InvalidRequestException


@convertibleclass
class RetrieveDashboardsRequestObject(BaseDashboardRequestObject):
    pass


@convertibleclass
class RetrieveDashboardRequestObject(BaseDashboardRequestObject):
    DASHBOARD_ID = "dashboardId"

    dashboardId: DashboardId = required_field()


@convertibleclass
class RetrieveGadgetDataRequestObject(BaseDashboardRequestObject):
    GADGET_ID = "gadgetId"
    DEPLOYMENT_IDS = "deploymentIds"
    ORGANIZATION_ID = "organizationId"

    gadgetId: GadgetId = required_field()
    deploymentIds: list[str] = default_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    organizationId: str = default_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, request_object):
        if request_object.resourceType == DashboardResourceType.DEPLOYMENT:
            raise NotImplementedError("Deployments are not allowed now")

    def check_permissions(self):
        super(RetrieveGadgetDataRequestObject, self).check_permissions()
        if self.resourceType == DashboardResourceType.ORGANIZATION:
            if request_deployment_ids := self.deploymentIds and set(self.deploymentIds):

                if not (
                    org_deployment_ids := self.submitter.organization.deploymentIds
                ):
                    raise PermissionDenied

                if not request_deployment_ids.issubset(org_deployment_ids):
                    raise PermissionDenied
