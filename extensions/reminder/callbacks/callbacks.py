from extensions.authorization.events import PostUserProfileUpdateEvent
from extensions.authorization.models.role.role import RoleName
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.reminder.models.reminder import UserModuleReminder
from sdk.calendar.service.calendar_service import CalendarService


def _get_module_reminder_translations(
    deployment: Deployment, new_language: str, module_id: str, module_config_id: str
):
    new_locales = deployment.get_localization(new_language)
    module = deployment.find_module_config(module_id, module_config_id)

    if module and module.notificationData:
        title = module.notificationData.title
        body = module.notificationData.body
        return new_locales.get(title), new_locales.get(body)

    return None, None


def update_reminders_language_localization(event: PostUserProfileUpdateEvent):
    if not (new_language := event.updated_fields.language):
        return
    if not event.previous_state:
        return

    old_language = event.previous_state.language
    user_id = event.previous_state.id
    role = event.previous_state.roles[0]

    if role.roleId != RoleName.USER or old_language == new_language:
        return

    calendar_service = CalendarService()
    deployment = DeploymentService().retrieve_deployment(
        deployment_id=role.resource_id()
    )
    for cal_event in calendar_service.retrieve_raw_events(
        userId=user_id, model=UserModuleReminder.__name__
    ):
        if not cal_event.moduleId or not cal_event.moduleConfigId:
            continue

        reminder_title, reminder_description = _get_module_reminder_translations(
            deployment, new_language, cal_event.moduleId, cal_event.moduleConfigId
        )
        if not (reminder_title and reminder_description):
            continue

        cal_event.title = reminder_title
        cal_event.description = reminder_description

        calendar_service.update_calendar_event(cal_event.id, cal_event, None)
