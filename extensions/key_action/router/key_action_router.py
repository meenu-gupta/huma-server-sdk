from flasgger import swag_from
from flask import jsonify, request, g

from extensions.authorization.events.update_stats_event import UpdateUserStatsEvent
from extensions.common.policies import get_user_route_read_policy
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.key_action.models.key_action_log import Action
from extensions.key_action.router.policies import get_write_events_policy
from extensions.key_action.use_case.key_action_requests import (
    CreateKeyActionLogRequestObject,
    RetrieveKeyActionsRequestObject,
    RetrieveKeyActionsTimeframeRequestObject,
    RetrieveExpiringKeyActionsRequestObject,
)
from extensions.key_action.use_case.key_action_responses import (
    RetrieveKeyActionsTimeframeResponseObject,
)
from extensions.key_action.use_case.retrieve_expiring_key_actions_case import (
    RetrieveExpiringKeyActionsUseCase,
)
from extensions.key_action.use_case.retrieve_key_actions_time_line_use_case import (
    RetrieveKeyActionsTimelineUseCase,
)
from extensions.key_action.use_case.retrieve_key_actions_use_case import (
    RetrieveKeyActionsUseCase,
)
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils import inject
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

key_action_route = IAMBlueprint(
    "key_action_route",
    __name__,
    url_prefix="/api/extensions/v1beta",
    policy=get_user_route_read_policy,
)


@key_action_route.route("/user/<user_id>/key-action/<key_action_id>", methods=["POST"])
@key_action_route.require_policy(get_write_events_policy)
@audit(Action.CreateKeyActionLog, target_key="key_action_id")
@swag_from(f"{SWAGGER_DIR}/create_key_action_log.yml")
def create_key_action_log(user_id: str, key_action_id: str):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CreateKeyActionLogRequestObject.PARENT_ID: key_action_id})
    log: CreateKeyActionLogRequestObject = CreateKeyActionLogRequestObject.from_dict(
        body
    )
    service = CalendarService()

    parent_event = service.retrieve_calendar_event(key_action_id)
    log.userId = parent_event.userId
    log.as_timezone(g.user.timezone or "UTC")

    action_id = service.create_calendar_event_log(log)
    event_bus = inject.instance(EventBusAdapter)
    event = UpdateUserStatsEvent(user_id=user_id)
    event_bus.emit(event)
    return jsonify({"id": action_id}), 201


@key_action_route.route("/user/<user_id>/key-action", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_key_actions.yml")
def retrieve_key_actions_for_user(user_id: str):
    body = dict(request.args) or {}
    body.update(
        {
            CalendarEvent.USER_ID: user_id,
            RetrieveKeyActionsRequestObject.TIMEZONE: g.user.timezone,
            RetrieveKeyActionsRequestObject.USER: g.authz_user,
        }
    )

    request_object = RetrieveKeyActionsRequestObject.from_dict(body)
    response = RetrieveKeyActionsUseCase().execute(request_object)

    return jsonify(response.value), 200


@key_action_route.route("/user/<user_id>/key-action/timeframe", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_key_actions_timeframe.yml")
def retrieve_key_actions_in_timeframe(user_id: str):
    body = {
        **(dict(request.args) or {}),
        CalendarEvent.USER_ID: user_id,
        RetrieveKeyActionsTimeframeRequestObject.TIMEZONE: g.user.timezone,
        RetrieveKeyActionsTimeframeRequestObject.USER: g.authz_user,
    }

    req = RetrieveKeyActionsTimeframeRequestObject.from_dict(body)
    response: RetrieveKeyActionsTimeframeResponseObject = (
        RetrieveKeyActionsTimelineUseCase().execute(req)
    )
    return jsonify(response.to_list()), 200


@key_action_route.route("/user/<user_id>/key-action/expiring", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_expiring_key_actions.yml")
def retrieve_expiring_key_actions_in_timeframe(user_id: str):
    only_enabled = dict(request.args or {}).get("onlyEnabled", "true")
    body = {
        **(dict(request.args) or {}),
        CalendarEvent.USER_ID: user_id,
        RetrieveKeyActionsTimeframeRequestObject.TIMEZONE: g.path_user.timezone,
        RetrieveKeyActionsTimeframeRequestObject.USER: g.authz_user,
        RetrieveExpiringKeyActionsRequestObject.ONLY_ENABLED: only_enabled,
    }

    req = RetrieveExpiringKeyActionsRequestObject.from_dict(body)
    response = RetrieveExpiringKeyActionsUseCase().execute(req)
    return jsonify(response.to_list()), 200
