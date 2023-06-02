import logging

from extensions.common.monitoring import report_exception
from extensions.module_result.exceptions import InvalidModuleConfiguration
from extensions.module_result.models.module_config import CustomModuleConfig
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.module_result.models.scheduled_event_utils import to_scheduled_events
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.router.custom_module_config_requests import (
    CreateOrUpdateCustomModuleConfigRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__name__)


class CreateOrUpdateCustomModuleConfigUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: CustomModuleConfigRepository):
        self._repo = repo

    def process_request(
        self, request_object: CreateOrUpdateCustomModuleConfigRequestObject
    ):
        module_config = request_object.to_dict(
            include_none=False,
            ignored_fields=[CreateOrUpdateCustomModuleConfigRequestObject.USER],
        )
        clinician_id = module_config.pop(request_object.CLINICIAN_ID)
        custom_module_config = CustomModuleConfig.from_dict(module_config)
        config_id = self._repo.create_or_update_custom_module_config(
            module_config_id=custom_module_config.id,
            module_config=custom_module_config,
            user_id=request_object.userId,
            clinician_id=clinician_id,
        )

        self._post_process(custom_module_config)
        return Response(value=config_id)

    def _post_process(self, config: CustomModuleConfig):
        if not config.schedule:
            return

        user = self.request_object.user.user
        timezone = user.timezone or "UTC"
        try:
            from sdk.calendar.service.calendar_service import CalendarService

            service = CalendarService()
            self._delete_old_events(config, service)
            self._create_scheduled_events(config, timezone, service)
        except InvalidModuleConfiguration as error:
            raise error
        except Exception as error:
            logger.warning(
                f"Error creating calendar for user #{user.id}. Error: {error}"
            )
            context = {"id": user.id, "timezone": timezone}
            report_exception(error, context_name="User", context_content=context)

    def _delete_old_events(self, module_config: CustomModuleConfig, service):
        user_id = self.request_object.userId
        filter_options = {
            ScheduledEvent.MODEL: ScheduledEvent.__name__,
            ScheduledEvent.USER_ID: user_id,
            f"{ScheduledEvent.EXTRA_FIELDS}.{ScheduledEvent.MODULE_CONFIG_ID}": module_config.id,
        }
        service.batch_delete_calendar_events(filter_options)
        logger.info(f"Old Scheduled events for user {user_id} cleared.")

    def _create_scheduled_events(
        self,
        module_config: CustomModuleConfig,
        timezone: str,
        service,
    ):
        user_id = self.request_object.userId
        schedule = module_config.schedule
        required_fields = (
            schedule.isoDuration,
            schedule.specificWeekDays,
            schedule.timesOfReadings,
        )
        if not all(required_fields):
            logger.info(
                f"Old Schedule format detected. Skipping calendar generation for user {user_id}"
            )
            return

        events = to_scheduled_events(module_config, timezone)
        for event in events:
            event.set_default_title_and_description(self.request_object.user)
            service.create_calendar_event(event, timezone)

        logger.info(f"{len(events)} Scheduled events created for user {user_id}")
