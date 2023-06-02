import logging

from flasgger import swag_from
from flask import Blueprint, request, jsonify, g

from sdk.auth.model.auth_user import AuthUser
from sdk.common.adapter.event_bus_adapter import check_event_before_call
from sdk.common.constants import SWAGGER_DIR
from sdk.common.localization.utils import Language
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.json_utils import replace_values
from sdk.inbox.events.auth_events import (
    InboxSearchAuthEvent,
    InboxSendAuthEvent,
    InboxConfirmAuthEvent,
)
from sdk.inbox.models.confirm_message import (
    ConfirmMessageRequestObject,
    ConfirmMessageResponseObject,
)
from sdk.inbox.models.message import Message
from sdk.inbox.models.search_message import (
    MessageSearchRequestObject,
    MessageSearchResponseObject,
)
from sdk.inbox.services.inbox_service import InboxService
from sdk.inbox.utils import translate_message_text_to_placeholder

api = Blueprint("inbox_route", __name__, url_prefix="/api/inbox/v1beta")
logger = logging.getLogger(__name__)


@api.route("/user/<user_id>/message/send", methods=["POST"])
@check_event_before_call(InboxSendAuthEvent)
@swag_from(f"{SWAGGER_DIR}/send_message_swag.yml")
def send_message(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)

    sender: AuthUser = g.auth_user
    sender_fullname = sender.displayName
    if hasattr(g, "user_full_name"):
        sender_fullname = g.user_full_name

    body[Message.SUBMITTER_ID] = sender.id
    body[Message.USER_ID] = user_id
    body[Message.SUBMITTER_NAME] = sender_fullname

    if not body.get(Message.CUSTOM) and hasattr(g, "authz_user"):
        body[Message.TEXT] = translate_message_text_to_placeholder(
            body.get(Message.TEXT), g.authz_user.localization
        )

    message = Message.from_dict(body)

    svc = InboxService()
    if hasattr(g, "path_user"):
        inserted_id = svc.send_message(message, g.path_user.language)
    else:
        inserted_id = svc.send_message(message, Language.EN)

    return jsonify({"id": inserted_id}), 201


@api.route("/user/<user_id>/message/search", methods=["POST"])
@check_event_before_call(InboxSearchAuthEvent)
@swag_from(f"{SWAGGER_DIR}/message_search_swag.yml")
def search_messages(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body[MessageSearchRequestObject.USER_ID] = user_id
    request_obj: MessageSearchRequestObject = MessageSearchRequestObject.from_dict(body)

    svc = InboxService()
    messages: MessageSearchResponseObject = svc.retrieve_messages(
        request_obj.userId,
        request_obj.submitterId,
        request_obj.skip,
        request_obj.limit,
        request_obj.custom,
    )
    if hasattr(g, "authz_user"):
        for message in messages.messages:
            message.text = replace_values(message.text, g.authz_user.localization)

    return jsonify(messages.to_dict()), 200


@api.route("/user/<user_id>/message/summary/search", methods=["POST"])
@check_event_before_call(InboxSearchAuthEvent)
@swag_from(f"{SWAGGER_DIR}/message_summary_swag.yml")
def summary_messages(user_id: str):
    svc = InboxService()
    response = svc.retrieve_submitters_first_messages(user_id)
    if hasattr(g, "authz_user"):
        response["messages"] = replace_values(
            response["messages"], g.authz_user.localization
        )

    return response, 200


@api.route("/message/confirm", methods=["POST"])
@check_event_before_call(InboxConfirmAuthEvent)
@swag_from(f"{SWAGGER_DIR}/message_confirm_swag.yml")
def confirm_messages():
    body = get_request_json_dict_or_raise_exception(request)
    user: AuthUser = g.auth_user
    request_object = ConfirmMessageRequestObject.from_dict(body)
    svc = InboxService()
    try:
        updated = svc.confirm_messages(user.id, request_object.messageIds)
    except PermissionError:
        return "Unauthorised User", 401
    result = ConfirmMessageResponseObject(updated).to_dict()
    return result, 201
