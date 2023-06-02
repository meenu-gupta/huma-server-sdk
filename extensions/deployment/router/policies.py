from flask import g, request

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import RoleAssignment
from extensions.exceptions import OrganizationDoesNotExist
from sdk.common.exceptions.exceptions import PermissionDenied


def match_deployment_or_wildcard():
    submitter: AuthorizedUser = g.authz_user
    deployment_id = request.view_args.get("deployment_id")
    if not deployment_id:
        return

    allowed_resources = ["*", deployment_id]
    submitter_resource = submitter.role_assignment.resource_id()
    if submitter_resource in allowed_resources:
        return

    try:
        submitter_resources = submitter.organization.deploymentIds or []
        for deployment_id in submitter_resources:
            if deployment_id in allowed_resources:
                return
    except OrganizationDoesNotExist:
        pass

    raise PermissionDenied


def wildcard_resource():
    submitter: AuthorizedUser = g.authz_user
    if not submitter.role_assignment.is_wildcard():
        raise PermissionDenied
