from flasgger import swag_from
from flask import request, jsonify, g

from extensions.appointment.router.appointment_requests import (
    RetrieveAppointmentRequestObject,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.common.policies import deny_not_self
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.reminder.models.reminder import UserModuleReminder, ReminderAction
from extensions.reminder.router.reminder_requests import (
    RetrieveRemindersRequestObject,
    CreateUserModuleReminderRequestObject,
    UpdateUserModuleReminderRequestObject,
    DeleteReminderRequestObject,
)
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
    validate_request_body_type_is_object,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "reminder_route",
    __name__,
    url_prefix="/api/extensions/v1beta",
    policy=[PolicyType.VIEW_OWN_EVENTS, deny_not_self],
)


@api.route("/user/<user_id>/reminder", methods=["POST"])
@api.require_policy(PolicyType.EDIT_OWN_EVENTS)
@audit(ReminderAction.CreateModuleReminder)
@swag_from(f"{SWAGGER_DIR}/create_module_user_reminder.yml")
def create_module_reminder_for_user(user_id: str):
    body = validate_request_body_type_is_object(request)
    path_user: AuthorizedUser = g.authz_path_user
    extras = {
        CreateUserModuleReminderRequestObject.LANGUAGE: path_user.get_language(),
        CreateUserModuleReminderRequestObject.MODEL: UserModuleReminder.__name__,
        CreateUserModuleReminderRequestObject.USER_ID: user_id,
        CreateUserModuleReminderRequestObject.DEPLOYMENT: path_user.deployment,
    }
    body.update(extras)
    reminder = CreateUserModuleReminderRequestObject.from_dict(body)

    timezone = path_user.user.timezone
    inserted_id = CalendarService().create_calendar_event(reminder, timezone)
    return jsonify({"id": inserted_id}), 201


@api.route("/user/<user_id>/reminder/<reminder_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_module_user_reminder.yml")
def retrieve_module_reminder_for_user(user_id, reminder_id):
    request_object = RetrieveAppointmentRequestObject.from_dict(
        {"appointmentId": reminder_id}
    )
    reminder = CalendarService().retrieve_calendar_event(request_object.appointmentId)
    return jsonify(reminder.to_dict(include_none=False)), 200


@api.route("/user/<user_id>/reminder/search", methods=["PUT"])
@swag_from(f"{SWAGGER_DIR}/retrieve_reminders.yml")
def retrieve_module_reminders(user_id):
    body = validate_request_body_type_is_object(request)
    request_obj: RetrieveRemindersRequestObject = (
        RetrieveRemindersRequestObject.from_dict(body)
    )
    service = CalendarService()
    model = UserModuleReminder
    kwargs = {f"{model.EXTRA_FIELDS}.{model.MODULE_ID}": request_obj.moduleId}
    if request_obj.moduleConfigId:
        extra = {
            f"{model.EXTRA_FIELDS}.{model.MODULE_CONFIG_ID}": request_obj.moduleConfigId
        }
        kwargs.update(extra)

    reminders = service.retrieve_raw_events(
        enabled=request_obj.enabled,
        userId=user_id,
        model=model.__name__,
        **kwargs,
    )
    result = []
    for reminder in reminders:
        reminder_dict = reminder.to_dict(
            ignored_fields=[UserModuleReminder.EXTRA_FIELDS]
        )
        result.append(remove_none_values(reminder_dict))
    return jsonify(result), 200


@api.route("/user/<user_id>/reminder/<reminder_id>", methods=["POST"])
@api.require_policy(PolicyType.EDIT_OWN_EVENTS)
@audit(ReminderAction.UpdateModuleReminder)
@swag_from(f"{SWAGGER_DIR}/update_module_user_reminder.yml")
def update_module_reminder_for_user(user_id, reminder_id):
    body = get_request_json_dict_or_raise_exception(request)
    service = CalendarService()
    old_reminder = service.retrieve_calendar_event(reminder_id)
    body.update(
        {
            UpdateUserModuleReminderRequestObject.USER_ID: user_id,
            UpdateUserModuleReminderRequestObject.MODEL: UserModuleReminder.__name__,
            UpdateUserModuleReminderRequestObject.OLD_REMINDER_MODULE_ID: old_reminder.moduleId,
        }
    )
    request_object = UpdateUserModuleReminderRequestObject.from_dict(body)
    user = g.path_user
    service.update_calendar_event(reminder_id, request_object, user.timezone)
    return jsonify({"id": reminder_id}), 200


@api.route("/user/<user_id>/reminder/<reminder_id>", methods=["DELETE"])
@api.require_policy(PolicyType.EDIT_OWN_EVENTS)
@audit(ReminderAction.DeleteModuleReminder, target_key="reminder_id")
@swag_from(f"{SWAGGER_DIR}/delete_reminder.yml")
def delete_own_reminder(user_id, reminder_id):
    request_object = DeleteReminderRequestObject.from_dict(
        {DeleteReminderRequestObject.REMINDER_ID: reminder_id}
    )
    CalendarService().delete_calendar_event(request_object.reminderId)
    return "", 204
