from flask import request, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.inject import autoparams


def get_identified_export_data():
    body = request.json or {}
    deidentified_request = body.get(ExportRequestObject.DEIDENTIFIED)
    if not deidentified_request:
        return PolicyType.VIEW_PATIENT_IDENTIFIER


@autoparams()
def check_identified_task_result(export_repo: ExportDeploymentRepository):
    export_process_id = request.view_args.get("export_process_id")
    export_process = export_repo.retrieve_export_process(export_process_id)
    if not export_process.exportParams.deIdentified:
        return PolicyType.VIEW_PATIENT_IDENTIFIER


def get_export_permission():
    authz_user: AuthorizedUser = g.authz_user
    body = get_request_json_dict_or_raise_exception(request)
    organization_id = body.get(ExportRequestObject.ORGANIZATION_ID)
    deployment_ids = body.get(ExportRequestObject.DEPLOYMENT_IDS)
    deployment_id = body.get(ExportRequestObject.DEPLOYMENT_ID)
    # checking if user has proper permission in all deployments he wants to export
    if deployment_ids:
        _check_user_deployment_role_export_permissions(authz_user, deployment_ids)
    elif organization_id:
        org_deployment_ids = _check_and_get_organization_deployment_ids(
            authz_user, organization_id
        )
        _check_user_deployment_role_export_permissions(authz_user, org_deployment_ids)
    elif deployment_id:
        _check_user_deployment_role_export_permissions(authz_user, [deployment_id])
    return PolicyType.EXPORT_PATIENT_DATA


def _check_and_get_organization_deployment_ids(
    authz_user: AuthorizedUser, organization_id
):
    is_wildcard_role = "*" in authz_user.deployment_ids()
    has_permission = organization_id in authz_user.organization_ids()
    if not any((is_wildcard_role, has_permission)):
        raise PermissionDenied
    authz_user = AuthorizedUser(authz_user.user, organization_id=organization_id)
    return authz_user.organization.deploymentIds or []


def _check_user_deployment_role_export_permissions(
    authz_user: AuthorizedUser, deployment_ids: list[str]
):
    user_deployment_ids = authz_user.deployment_ids()
    is_wildcard_role = "*" in user_deployment_ids
    has_permission = all(_id in user_deployment_ids for _id in deployment_ids)
    if not any((is_wildcard_role, has_permission)):
        raise PermissionDenied
    _check_deployment_roles_has_export_permission(authz_user, deployment_ids)


def _check_deployment_roles_has_export_permission(
    authz_user: AuthorizedUser, deployment_ids: list[str]
):
    body = request.json or {}
    deidentified_request = body.get(ExportRequestObject.DEIDENTIFIED)
    permissions = [PolicyType.EXPORT_PATIENT_DATA]
    if not deidentified_request:
        permissions.append(PolicyType.VIEW_PATIENT_IDENTIFIER)
    for deployment_id in deployment_ids:
        authz_deployment_user = AuthorizedUser(authz_user.user, deployment_id)
        role = authz_deployment_user.get_role()

        if not role.has(permissions):
            raise PermissionDenied
