from typing import Iterable
import logging
from datetime import datetime

import pytz

from extensions.authorization.di.components import PostCreateUserEvent
from extensions.authorization.events import PostUserProfileUpdateEvent
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.retrieve_profiles_use_case import (
    RetrieveProfilesUseCase,
)
from extensions.common.monitoring import report_exception
from extensions.deployment.events import (
    PostCreateKeyActionConfigEvent,
    PostUpdateKeyActionConfigEvent,
    PostDeleteKeyActionConfigEvent,
)
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.use_case.key_action_requests import (
    CreateKeyActionLogRequestObject,
)
from extensions.key_action.utils import (
    key_action_config_filter_by_id,
    key_action_config_filter_by_trigger,
)
from extensions.module_result.event_bus.post_create_primitive import (
    PostCreatePrimitiveEvent,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.calendar.service.calendar_service import CalendarService
from sdk.calendar.utils import get_dt_from_str, now_no_seconds
from sdk.common.constants import VALUE_IN
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.validators import utc_str_val_to_field

logger = logging.getLogger("keyActionCallbacks")


def create_log_callback(event: PostCreatePrimitiveEvent):
    if not event.module_config_id:
        return

    logger.debug(
        f"Creating key action log for {event.module_id}/{event.primitive_name}"
    )
    service = CalendarService()
    options = {
        KeyAction.MODEL: {VALUE_IN: [KeyAction.__name__, ScheduledEvent.__name__]},
        KeyAction.USER_ID: event.user_id,
        f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_ID}": event.module_id,
        f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_CONFIG_ID}": event.module_config_id,
    }

    user = AuthorizationService().retrieve_simple_user_profile(event.user_id)
    timezone = pytz.timezone(user.timezone)
    compare_dt = get_dt_from_str(event.create_date_time)
    events = service.retrieve_calendar_events(compare_dt, timezone, **options)

    enabled_events = list(filter(lambda x: x.enabled, events))
    if not enabled_events:
        return
    enabled_events.sort(reverse=True, key=lambda x: x.startDateTime)
    matched_event = next(iter(enabled_events))
    _dict = {
        CreateKeyActionLogRequestObject.MODEL: matched_event.model,
        CreateKeyActionLogRequestObject.USER_ID: user.id,
        CreateKeyActionLogRequestObject.PARENT_ID: matched_event.id,
        CreateKeyActionLogRequestObject.START_DATE_TIME: matched_event.startDateTime,
        CreateKeyActionLogRequestObject.END_DATE_TIME: matched_event.endDateTime,
    }
    log: CreateKeyActionLogRequestObject = CreateKeyActionLogRequestObject.from_dict(
        _dict
    )
    log.as_timezone(user.timezone)
    service.create_calendar_event_log(log)
    logger.debug(f"Key action log for {event.module_id} created")


def on_user_delete_callback(event: DeleteUserEvent):
    service = CalendarService()
    try:
        service.delete_user_events(session=event.session, user_id=event.user_id)
    except Exception as error:
        logger.error(f"Error on deleting user events: {str(error)}")
        report_exception(
            error,
            context_name="DeleteUserEvents",
            context_content={"userId": event.user_id},
        )
        raise error


def create_key_actions_events(event: PostCreateUserEvent):
    authz_user = AuthorizedUser(event.user)
    if not authz_user.is_user():
        return

    deployment = DeploymentService().retrieve_deployment_config(authz_user)
    if not (deployment.keyActionsEnabled and deployment.keyActions):
        return
    key_actions: Iterable[KeyActionConfig] = key_action_config_filter_by_trigger(
        deployment.keyActions, KeyActionConfig.Trigger.SIGN_UP
    )
    start = now_no_seconds()

    service = CalendarService()
    user = authz_user.user
    for action in key_actions:
        try:
            generator = KeyActionGenerator(user, start, deployment.id)
            cal_event = generator.build_key_action_from_config(action)
            service.create_calendar_event(cal_event, user.timezone)
        except Exception as error:
            logger.error(
                f"Key action was not created for user #{authz_user.user.email}. Error: {error}"
            )
            report_exception(
                error,
                context_name="CreateCalendarEvent",
                context_content={
                    "keyActionConfig": action,
                    "userId": user.id,
                    "startDate": start,
                    "deploymentId": deployment.id,
                },
            )


def create_key_action_config_callback(event: PostCreateKeyActionConfigEvent):
    """
    Create key actions for all users based on key action config.
    Skip users that don't have connected module config enabled.
    """
    deployment_id = event.deployment_id
    request_obj = RetrieveProfilesRequestObject(clean=True, deploymentId=deployment_id)
    use_case = RetrieveProfilesUseCase()
    response = use_case.execute(request_obj)
    users = [User.from_dict(user) for user in response.value]
    deployment = use_case.deployment
    if not deployment.keyActionsEnabled:
        return

    filtered_actions = key_action_config_filter_by_id(
        deployment.keyActions, event.key_action_config_id
    )
    key_action: KeyActionConfig = next(filtered_actions, None)
    if not key_action:
        return

    if key_action.trigger == KeyActionConfig.Trigger.MANUAL:
        return

    service = CalendarService()
    for index, user in enumerate(users):
        care_plan_id = user.carePlanGroupId
        if care_plan_id and deployment.carePlanGroup:
            group = deployment.carePlanGroup.get_care_plan_group_by_id(care_plan_id)
            enabled_modules = deployment.patch_module_configs_by_group(group)
            enabled_ids = [module.id for module in enabled_modules]
            if key_action.moduleConfigId not in enabled_ids:
                continue

        if key_action.trigger == KeyActionConfig.Trigger.SIGN_UP:
            trigger_dt = utc_str_val_to_field(user.createDateTime)
        elif (
            key_action.trigger == KeyActionConfig.Trigger.SURGERY
            and user.surgeryDateTime
        ):
            dt = datetime.combine(user.surgeryDateTime, datetime.min.time())
            trigger_dt = utc_str_val_to_field(dt)
        else:
            continue
        generator = KeyActionGenerator(user, trigger_dt, deployment.id)
        cal_event = generator.build_key_action_from_config(key_action)
        service.create_calendar_event(cal_event, user.timezone)


def create_surgery_key_action_on_user_change(event: PostUserProfileUpdateEvent):
    if not event.updated_fields.surgeryDateTime:
        return

    if event.previous_state:
        user = event.previous_state
        if event.updated_fields.surgeryDateTime == event.previous_state.surgeryDateTime:
            return
    else:
        user = AuthorizationService().retrieve_user_profile(event.updated_fields.id)

    authz_user = AuthorizedUser(user)

    if not authz_user.is_user():
        return

    deployment = DeploymentService().retrieve_deployment_config(authz_user)
    if not deployment.keyActionsEnabled:
        return

    key_actions: Iterable[KeyActionConfig] = key_action_config_filter_by_trigger(
        deployment.keyActions, KeyActionConfig.Trigger.SURGERY
    )

    start = event.updated_fields.surgeryDateTime
    for action in key_actions:
        _delete_calendar_events_for_user_by_key_action_id(action.id, user.id)
        _create_calendar_event(user, action, start, deployment.id)


def update_key_actions_on_care_plan_group_change(event: PostUserProfileUpdateEvent):
    """
    Remove old key actions on user care plan group update.
    Create new key actions based on new care plan group.
    """
    user = event.updated_fields
    if not user.carePlanGroupId:
        return

    user = AuthorizationService().retrieve_user_profile(user_id=user.id)
    authz_user = AuthorizedUser(user)
    deployment = DeploymentService().retrieve_deployment_config(authz_user)
    CalendarService().batch_delete_calendar_events(
        {KeyAction.USER_ID: user.id, KeyAction.MODEL: KeyAction.__name__}
    )
    if not (deployment.keyActionsEnabled and deployment.keyActions):
        return

    error_msg = "Unsupported trigger %s. Key action #%s was not created for user #%s %s"
    for config in deployment.keyActions:
        if config.trigger == KeyActionConfig.Trigger.SIGN_UP:
            start = user.createDateTime
        elif config.trigger == KeyActionConfig.Trigger.SURGERY and user.surgeryDateTime:
            start = user.surgeryDateTime
        else:
            user_data = user.email or user.phoneNumber
            logger.warning(error_msg % config.trigger, config.id, user.id, user_data)
            continue

        _create_calendar_event(user, config, start, deployment.id)


def _delete_calendar_events_for_user_by_key_action_id(action_id: str, user_id: str):
    CalendarService().batch_delete_calendar_events(
        {
            f"{KeyAction.EXTRA_FIELDS}.{KeyAction.KEY_ACTION_CONFIG_ID}": action_id,
            f"{KeyAction.USER_ID}": user_id,
        }
    )


def _create_calendar_event(user, action, start_date, deployment_id):
    service = CalendarService()
    try:
        generator = KeyActionGenerator(user, start_date, deployment_id)
        cal_event = generator.build_key_action_from_config(action)
        service.create_calendar_event(cal_event, user.timezone)
    except Exception as error:
        logger.error(
            f"Key action was not created for user #{user.email}." f" Error: {error}"
        )
        report_exception(
            error,
            context_name="CreateCalendarEvent",
            context_content={
                "keyActionConfig": action,
                "userId": user.id,
                "startDate": start_date,
                "deploymentId": deployment_id,
            },
        )


def update_key_actions_events(event: PostUpdateKeyActionConfigEvent):
    deployment = DeploymentService().retrieve_deployment(event.deployment_id)
    # search keyActionConfig by id
    filtered_actions = key_action_config_filter_by_id(
        deployment.keyActions, event.key_action_config_id
    )
    key_action_config: KeyActionConfig = next(filtered_actions, None)
    if not key_action_config:
        raise ObjectDoesNotExist

    if key_action_config.trigger == KeyActionConfig.Trigger.MANUAL:
        return

    service = CalendarService()
    events = service.retrieve_raw_events(
        **{
            f"{KeyAction.EXTRA_FIELDS}.{KeyAction.KEY_ACTION_CONFIG_ID}": key_action_config.id
        }
    )
    users = {event.userId for event in events}
    users = AuthorizationService().retrieve_user_profiles_by_ids(users)
    users = {user.id: user for user in users}
    for event in events:
        user: User = users.pop(event.userId, None)
        if user:
            if key_action_config.trigger == KeyActionConfig.Trigger.SIGN_UP:
                trigger_dt = utc_str_val_to_field(user.createDateTime)
            elif (
                key_action_config.trigger == KeyActionConfig.Trigger.SURGERY
                and user.surgeryDateTime
            ):
                dt = datetime.combine(user.surgeryDateTime, datetime.min.time())
                trigger_dt = utc_str_val_to_field(dt)
            else:
                continue
            generator = KeyActionGenerator(user, trigger_dt, deployment.id)
            cal_event = generator.build_key_action_from_config(key_action_config)
            service.update_calendar_event(event.id, cal_event, user.timezone)
        else:
            logger.debug(
                f"Update key action error: User {event.userId} not found in DB."
            )


def delete_key_action_config_callback(event: PostDeleteKeyActionConfigEvent):
    CalendarService().batch_delete_calendar_events(
        {f"{KeyAction.EXTRA_FIELDS}.{KeyAction.KEY_ACTION_CONFIG_ID}": event.id}
    )
