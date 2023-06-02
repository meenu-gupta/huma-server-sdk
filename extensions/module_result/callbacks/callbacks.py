import logging

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.policies import check_proxy_permission
from extensions.deployment.events import PostDeploymentUpdateEvent
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.event_bus.post_retrieve_primitive import (
    PostRetrievePrimitiveEvent,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.module_result.service.module_result_service import ModuleResultService
from sdk.auth.events.delete_user_event import DeleteUserEvent
from extensions.common.monitoring import report_exception
from sdk.common.utils import inject

logger = logging.getLogger(__name__)


def on_user_delete_callback(event: DeleteUserEvent):
    service = ModuleResultService()

    try:
        service.delete_user_primitive(session=event.session, user_id=event.user_id)
    except Exception as error:
        logger.error(f"Error on deleting user primitives: {str(error)}")
        report_exception(
            error,
            context_name="DeleteUserPrimitive",
            context_content={"userId": event.user_id},
        )
        raise error


def disable_schedule_events_callback(event: PostDeploymentUpdateEvent):
    try:
        from sdk.calendar.service.calendar_service import CalendarService

        service = CalendarService()
    except Exception:
        return

    return disable_schedule_events(event.deployment, service)


def disable_schedule_events(deployment: Deployment, service):
    """
    @param deployment: deployment object with update
    @param service: CalendarService
    """
    if not (deployment.features and deployment.features.personalizedConfig is not None):
        return

    auth_repo = inject.instance(AuthorizationRepository)
    users = auth_repo.retrieve_user_ids_in_deployment(deployment.id)
    filter_options = {
        ScheduledEvent.MODEL: ScheduledEvent.__name__,
        ScheduledEvent.USER_ID: users,
    }
    service.update_events_status(filter_options, deployment.features.personalizedConfig)


def check_retrieve_permissions(event: PostRetrievePrimitiveEvent):
    check_proxy_permission(str(event.deployment_id))
