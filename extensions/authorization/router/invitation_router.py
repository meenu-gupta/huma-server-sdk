from flasgger import swag_from
from flask import request, jsonify, g

from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    ResendInvitationsRequestObject,
    GetInvitationLinkRequestObject,
    DeleteInvitationRequestObject,
    RetrieveInvitationsRequestObject,
    ResendInvitationsListRequestObject,
    DeleteInvitationsListRequestObject,
)
from extensions.authorization.router.policies import (
    get_invitations_policy,
    get_delete_invitation_list_policy,
    get_resend_invitation_list_policy,
    get_resend_invitation_policy,
)
from extensions.authorization.router.policies import (
    get_list_invitations_policy,
    get_delete_invitation_policy,
)
from extensions.authorization.use_cases.invitation_use_cases import (
    SendInvitationsUseCase,
    ResendInvitationsUseCase,
    GetInvitationLinkUseCase,
    DeleteInvitationUseCase,
    RetrieveInvitationsUseCase,
    RetrieveInvitationsV1UseCase,
    ResendInvitationsListUseCase,
    DeleteInvitationsListUseCase,
)
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "invitation_route",
    __name__,
    url_prefix="/api/extensions/v1beta/deployment",
    policy=get_invitations_policy,
)

api_v1 = IAMBlueprint(
    "invitation_route_v1",
    __name__,
    url_prefix="/api/extensions/v1/deployment",
    policy=get_invitations_policy,
)


@api.route("/send-invitation", methods=["POST"])
@audit(AuthorizationAction.SendInvitation)
@swag_from(f"{SWAGGER_DIR}/send_invitation.yml")
def send_user_invitation():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_data[SendInvitationsRequestObject.SUBMITTER] = g.authz_user
    request_object = SendInvitationsRequestObject.from_dict(request_data)
    request_object.check_permission(g.authz_user)
    response_object = SendInvitationsUseCase().execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/resend-invitation", methods=["POST"])
@api.require_policy(get_resend_invitation_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/resend_invitation.yml")
def resend_user_invitation():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_object = ResendInvitationsRequestObject.from_dict(request_data)
    ResendInvitationsUseCase().execute(request_object)
    return "", 200


@api.route("/resend-invitation-list", methods=["POST"])
@audit(AuthorizationAction.ResendBulkEmailInvitation)
@api.require_policy(get_resend_invitation_list_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/resend_invitation_list.yml")
def resend_user_invitation_list():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_object = ResendInvitationsListRequestObject.from_dict(request_data)
    result_object = ResendInvitationsListUseCase().execute(request_object)
    return jsonify(result_object.value), 200


@api.route("/invitation-link", methods=["POST"])
@audit(AuthorizationAction.GetInvitationLink)
@swag_from(f"{SWAGGER_DIR}/get_invitation_link.yml")
def get_invitation_link():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_data[GetInvitationLinkRequestObject.SENDER_ID] = g.authz_user.id
    request_object = GetInvitationLinkRequestObject.from_dict(request_data)
    response_obj = GetInvitationLinkUseCase().execute(request_object)
    return jsonify(response_obj.value.to_dict()), 200


@api.route("/invitation/<invitation_id>", methods=["DELETE"])
@api.require_policy(get_delete_invitation_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/delete_invitation.yml")
def delete_invitation(invitation_id: str):
    request_data = {DeleteInvitationRequestObject.INVITATION_ID: invitation_id}
    request_object = DeleteInvitationRequestObject.from_dict(request_data)
    DeleteInvitationUseCase().execute(request_object)
    return "", 204


@api.route("/invitation", methods=["DELETE"])
@audit(AuthorizationAction.DeleteBulkInvitation)
@api.require_policy(get_delete_invitation_list_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/delete_invitation_list.yml")
def delete_invitation_list():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_object = DeleteInvitationsListRequestObject.from_dict(request_data)
    response_object = DeleteInvitationsListUseCase().execute(request_object)
    return jsonify(response_object.value), 200


@api.route("/invitations", methods=["POST"])
@api.require_policy(get_list_invitations_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_invitations.yml")
def retrieve_invitations():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_data[RetrieveInvitationsRequestObject.SUBMITTER] = g.authz_user
    request_object = RetrieveInvitationsRequestObject.from_dict(request_data)
    response_object = RetrieveInvitationsUseCase().execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api_v1.route("/invitations", methods=["POST"])
@api_v1.require_policy(get_list_invitations_policy, override=True)
@swag_from(f"{SWAGGER_DIR}/retrieve_invitations_v1.yml")
def retrieve_invitations_v1():
    request_data = get_request_json_dict_or_raise_exception(request)
    request_data[RetrieveInvitationsRequestObject.SUBMITTER] = g.authz_user
    request_object = RetrieveInvitationsRequestObject.from_dict(request_data)
    response_object = RetrieveInvitationsV1UseCase().execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200
