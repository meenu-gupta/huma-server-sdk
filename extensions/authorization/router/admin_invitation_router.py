from flasgger import swag_from
from flask import request, jsonify, g

from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.router.admin_invitation_request_objects import (
    SendAdminInvitationsRequestObject,
)
from extensions.authorization.router.policies import admin_invitation_policy
from extensions.authorization.use_cases.admin_invitation_use_cases import (
    SendAdminInvitationsUseCase,
)
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "admin_invitation_route",
    __name__,
    url_prefix="/api/extensions/v1beta/admin",
    policy=admin_invitation_policy,
)


@api.post("/send-invitation")
@audit(AuthorizationAction.SendAdminInvitation)
@swag_from(f"{SWAGGER_DIR}/send_admin_invitations.yml")
def send_admin_invitations():
    body = get_request_json_dict_or_raise_exception(request)
    body.update({SendAdminInvitationsRequestObject.SUBMITTER: g.authz_user})
    request_object = SendAdminInvitationsRequestObject.from_dict(body)
    response_object = SendAdminInvitationsUseCase().execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200
