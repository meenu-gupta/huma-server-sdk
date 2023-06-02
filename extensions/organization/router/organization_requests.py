from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role
from extensions.common.sort import SortField
from extensions.dashboard.models.dashboard import DashboardId
from extensions.deployment.models.status import Status
from extensions.organization.models.organization import Organization
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    must_not_be_present,
    must_be_present,
    validate_object_id,
    validate_object_ids,
)


@convertibleclass
class CreateOrganizationRequestObject(Organization):
    ID = "id"
    SUBMITTER_ID = "submitterId"

    submitterId: str = required_field(metadata=meta(validate_object_id))

    def post_init(self):
        if not self.dashboardId:
            self.dashboardId = DashboardId.ORGANIZATION_OVERVIEW

    @classmethod
    def validate(cls, organization):
        must_not_be_present(
            id=organization.id,
            updateDateTime=organization.updateDateTime,
            deploymentIds=organization.deploymentIds,
            createDateTime=organization.createDateTime,
            roles=organization.roles,
            targetConsented=organization.targetConsented,
        )
        must_be_present(
            name=organization.name,
        )
        if (
            organization.privacyPolicyUrl
            or organization.termAndConditionUrl
            or organization.eulaUrl
        ):
            must_be_present(
                privacyPolicyUrl=organization.privacyPolicyUrl,
                termAndConditionUrl=organization.termAndConditionUrl,
                eulaUrl=organization.eulaUrl,
            )
        else:
            must_be_present(
                privacyPolicyObject=organization.privacyPolicyObject,
                termAndConditionObject=organization.termAndConditionObject,
                eulaObject=organization.eulaObject,
            )


@convertibleclass
class UpdateOrganizationRequestObject(Organization):
    ID = "id"

    @classmethod
    def validate(cls, organization):
        must_not_be_present(
            createDateTime=organization.createDateTime,
            updateDateTime=organization.updateDateTime,
            deploymentIds=organization.deploymentIds,
            roles=organization.roles,
        )
        must_be_present(id=organization.id)


@convertibleclass
class LinkDeploymentRequestObject:
    ID = "id"
    ORGANIZATION_ID = "organizationId"

    organizationId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class LinkDeploymentsRequestObject:
    ID = "id"
    ORGANIZATION_ID = "organizationId"
    DEPLOYMENT_IDS = "deploymentIds"

    organizationId: str = required_field(metadata=meta(validate_object_id))
    deploymentIds: list[str] = required_field(metadata=meta(validate_object_ids))


@convertibleclass
class RetrieveOrganizationRequestObject:
    ORGANIZATION_ID = "organizationId"
    organizationId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UnlinkDeploymentsRequestObject(LinkDeploymentsRequestObject):
    pass


@convertibleclass
class DeleteOrganizationRequestObject:
    ORGANIZATION_ID = "organizationId"
    SUBMITTER_ID = "submitterId"

    organizationId: str = required_field(metadata=meta(validate_object_id))
    submitterId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UnlinkDeploymentRequestObject:
    organizationId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveOrganizationsRequestObject:
    SKIP = "skip"
    LIMIT = "limit"
    SEARCH_CRITERIA = "searchCriteria"
    SORT = "sort"
    NAME_CONTAINS = "nameContains"
    STATUS = "status"

    skip: int = required_field()
    limit: int = required_field()
    sort: list[SortField] = default_field()
    nameContains: str = default_field()
    searchCriteria: str = default_field()
    status: list[Status] = default_field()


@convertibleclass
class OrganizationRoleUpdateObject:
    ORGANIZATION_ID = "organizationId"
    ROLES = "roles"

    organizationId: str = required_field(metadata=meta(validate_object_id))
    roles: list[Role] = required_field()

    @classmethod
    def validate(cls, instance):
        default_roles = inject.instance(DefaultRoles)
        roles = instance.roles or []
        role_names = set(role.name for role in roles)
        if len(role_names) != len(instance.roles):
            raise InvalidRequestException("Can't create multiple roles with same name.")
        msg_template = "Custom role name cannot be one of default roles %s"
        for role in roles:
            must_be_present(
                name=role.name, permissions=role.has_extra_permissions() or None
            )
            is_default_role = role.name.lower() in {x.lower() for x in default_roles}
            if is_default_role:
                msg = msg_template % f"[{', '.join(default_roles)}]"
                raise InvalidRequestException(msg)


@convertibleclass
class UpdateOrganizationTargetConsentedRequestObject:
    ORGANIZATION_ID = "organizationId"
    ORGANIZATION_IDS = "organizationIds"

    organizationIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(metadata=meta(validate_object_id))
