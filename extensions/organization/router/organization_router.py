from flasgger import swag_from
from flask import request, jsonify, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.deployment.router.policies import wildcard_resource
from extensions.organization.models.organization import (
    OrganizationAction,
    OrganizationWithDeploymentInfo,
)
from extensions.organization.router.organization_requests import (
    CreateOrganizationRequestObject,
    RetrieveOrganizationRequestObject,
    UpdateOrganizationRequestObject,
    DeleteOrganizationRequestObject,
    RetrieveOrganizationsRequestObject,
    UnlinkDeploymentRequestObject,
    LinkDeploymentRequestObject,
    OrganizationRoleUpdateObject,
    LinkDeploymentsRequestObject,
    UnlinkDeploymentsRequestObject,
)
from extensions.organization.router.policies import match_organization_or_wildcard
from extensions.organization.use_case.create_organization_use_case import (
    CreateOrganizationUseCase,
)
from extensions.organization.use_case.create_role_use_case import (
    CreateOrUpdateRolesUseCase,
)
from extensions.organization.use_case.delete_organization_use_case import (
    DeleteOrganizationUseCase,
)
from extensions.organization.use_case.link_deployment_use_case import (
    LinkDeploymentUseCase,
)
from extensions.organization.use_case.link_deployments_use_case import (
    LinkDeploymentsUseCase,
)
from extensions.organization.use_case.retrieve_organization_use_case import (
    RetrieveOrganizationUseCase,
)
from extensions.organization.use_case.retrieve_organizations_use_case import (
    RetrieveOrganizationsUseCase,
)
from extensions.organization.use_case.unlink_deployment_use_case import (
    UnlinkDeploymentUseCase,
)
from extensions.organization.use_case.unlink_deployments_use_case import (
    UnlinkDeploymentsUseCase,
)
from extensions.organization.use_case.update_organization_use_case import (
    UpdateOrganizationUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.common_functions_utils import deprecated
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

organization_route = IAMBlueprint(
    "organisation_route",
    __name__,
    url_prefix="/api/extensions/v1beta/organization",
    policy=match_organization_or_wildcard,
)


@organization_route.route("", methods=["POST"])
@organization_route.require_policy(PolicyType.CREATE_ORGANIZATION)
@audit(OrganizationAction.CreateOrganization)
@swag_from(f"{SWAGGER_DIR}/create_organization.yml")
def create_organization():
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CreateOrganizationRequestObject.SUBMITTER_ID: g.user.id})
    request_object = CreateOrganizationRequestObject.from_dict(body)
    response = CreateOrganizationUseCase().execute(request_object)

    return jsonify({CreateOrganizationRequestObject.ID: response.value}), 201


@organization_route.route("/<organization_id>", methods=["GET"])
@organization_route.require_policy(PolicyType.VIEW_ORGANIZATION)
@swag_from(f"{SWAGGER_DIR}/retrieve_organization.yml")
def retrieve_organization(organization_id):
    request_object = RetrieveOrganizationRequestObject.from_dict(
        {RetrieveOrganizationRequestObject.ORGANIZATION_ID: organization_id}
    )
    organization: OrganizationWithDeploymentInfo = (
        RetrieveOrganizationUseCase().execute(request_object).value
    )

    return jsonify(organization.to_dict()), 200


@organization_route.route("/<organization_id>", methods=["PUT"])
@organization_route.require_policy(PolicyType.EDIT_ORGANIZATION)
@audit(OrganizationAction.UpdateOrganization, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/update_organization.yml")
def update_organization(organization_id):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({UpdateOrganizationRequestObject.ID: organization_id})
    request_object = UpdateOrganizationRequestObject.from_dict(body)
    response = UpdateOrganizationUseCase().execute(request_object)

    return jsonify({UpdateOrganizationRequestObject.ID: response.value}), 200


@organization_route.route("/<organization_id>", methods=["DELETE"])
@organization_route.require_policy(PolicyType.DELETE_ORGANIZATION)
@audit(OrganizationAction.DeleteOrganization, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/delete_organization.yml")
def delete_organization(organization_id):
    data = {
        DeleteOrganizationRequestObject.ORGANIZATION_ID: organization_id,
        DeleteOrganizationRequestObject.SUBMITTER_ID: g.user.id,
    }
    request_object = DeleteOrganizationRequestObject.from_dict(data)
    DeleteOrganizationUseCase().execute(request_object)

    return "", 204


@deprecated("Use `/link-deployments` instead.")
@organization_route.route("/<organization_id>/link-deployment", methods=["POST"])
@organization_route.require_policy(PolicyType.EDIT_ORGANIZATION)
@audit(OrganizationAction.LinkDeployment, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/link_deployment.yml")
def link_deployment(organization_id):
    """@deprecated"""

    body = get_request_json_dict_or_raise_exception(request)
    body.update({LinkDeploymentRequestObject.ORGANIZATION_ID: organization_id})

    request_object = LinkDeploymentRequestObject.from_dict(body)
    response = LinkDeploymentUseCase().execute(request_object)

    return jsonify({LinkDeploymentRequestObject.ID: response.value}), 200


@organization_route.route("/<organization_id>/link-deployments", methods=["POST"])
@organization_route.require_policy(PolicyType.EDIT_ORGANIZATION)
@audit(OrganizationAction.LinkDeployment, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/link_deployments.yml")
def link_deployments(organization_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object = LinkDeploymentsRequestObject.from_dict(
        {
            **body,
            LinkDeploymentsRequestObject.ORGANIZATION_ID: organization_id,
        }
    )
    response = LinkDeploymentsUseCase().execute(request_object)
    return jsonify({LinkDeploymentsRequestObject.ID: response.value}), 200


@organization_route.route(
    "/<organization_id>/deployment/<deployment_id>", methods=["DELETE"]
)
@organization_route.require_policy(PolicyType.EDIT_ORGANIZATION)
@audit(OrganizationAction.UnLinkDeployment, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/unlink_deployment.yml")
def unlink_deployment(organization_id, deployment_id):
    request_object = UnlinkDeploymentRequestObject(
        organizationId=organization_id, deploymentId=deployment_id
    )
    UnlinkDeploymentUseCase().execute(request_object)

    return "", 204


@organization_route.route("/search", methods=["POST"])
@organization_route.require_policy([PolicyType.VIEW_ORGANIZATION, wildcard_resource])
@swag_from(f"{SWAGGER_DIR}/retrieve_organizations.yml")
def retrieve_organizations():
    body = get_request_json_dict_or_raise_exception(request)
    request_object: RetrieveOrganizationsRequestObject = (
        RetrieveOrganizationsRequestObject.from_dict(body)
    )

    response = RetrieveOrganizationsUseCase().execute(request_object)

    return jsonify(response.value), 200


@organization_route.route("/<organization_id>/role", methods=["PUT"])
@organization_route.require_policy(PolicyType.EDIT_CUSTOM_ROLES)
@audit(OrganizationAction.CreateOrUpdateRoles, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/organization_update_role.yml")
def create_or_update_organization_role(organization_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({OrganizationRoleUpdateObject.ORGANIZATION_ID: organization_id})
    request_object: OrganizationRoleUpdateObject = (
        OrganizationRoleUpdateObject.from_dict(body)
    )
    response = CreateOrUpdateRolesUseCase().execute(request_object)

    return {"id": response.value}, 200


@organization_route.route("/<organization_id>/unlink-deployments", methods=["POST"])
@organization_route.require_policy(PolicyType.EDIT_ORGANIZATION)
@audit(OrganizationAction.UnLinkDeployment, target_key="organization_id")
@swag_from(f"{SWAGGER_DIR}/unlink_deployments.yml")
def unlink_deployments(organization_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object = UnlinkDeploymentsRequestObject.from_dict(
        {
            **body,
            UnlinkDeploymentsRequestObject.ORGANIZATION_ID: organization_id,
        }
    )
    response = UnlinkDeploymentsUseCase().execute(request_object)
    return jsonify({UnlinkDeploymentsRequestObject.ID: response.value}), 200
