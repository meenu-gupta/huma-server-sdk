from flask import g, request

from extensions.authorization.models.authorized_user import AuthorizedUser
from sdk.common.exceptions.exceptions import PermissionDenied


def match_organization_or_wildcard():
    submitter: AuthorizedUser = g.authz_user
    organization_id = request.view_args.get("organization_id")
    if not organization_id:
        return

    allowed_resources = ["*", organization_id]
    submitter_resource = submitter.role_assignment.resource_id()
    if submitter_resource not in allowed_resources:
        raise PermissionDenied
