import logging

from celery.schedules import crontab

from sdk.calendar.events import RequestUsersTimezonesEvent
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.service.calendar_service import CalendarService
from sdk.calendar.utils import now_no_seconds
from sdk.celery.app import celery_app
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import ClassNotRegisteredException
from sdk.common.utils import inject

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Call prepare_reminders task every minute
    sender.add_periodic_task(
        crontab(minute="*"),
        prepare_events_and_execute.s(),
        name="Event executor",
    )

    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        prepare_events_for_next_day.s(),
        name="New users handler",
    )


@celery_app.task(expires=24 * 60 * 60)
def prepare_events_for_next_day():
    CalendarService().calculate_and_save_next_day_events(get_timezones())


@celery_app.task(expires=60)
def prepare_events_and_execute():
    """
    Query events that needs execution and execute them in batches by 10 items.
    Removes successfully executed events from the db.
    """
    service = CalendarService()
    now = now_no_seconds()
    events = service.retrieve_next_day_events({CalendarEvent.START_DATE_TIME: now})
    event_dicts = [event_to_typed_dict(e) for e in events]

    for i in range(0, len(event_dicts), 10):
        execute_events.delay(event_dicts[i : i + 10])

    service.batch_delete_next_day_events([e.id for e in events])


def event_to_typed_dict(event: CalendarEvent) -> dict:
    return {
        **event.to_dict(include_none=False, ignored_fields=[event.EXTRA_FIELDS]),
        "type": event.model,
    }


@celery_app.task
def execute_events(events: list[dict]):
    user_id = None
    for event_dict in events:
        try:
            user_id = user_id or event_dict["userId"]
            event_class = CalendarEvent.child(event_dict["type"])
            event = event_class.from_dict(event_dict)
            event.execute(run_async=False)
            logger.debug(f"SCHEDULER: Event.execute finished for user {event.userId}.")
        except ClassNotRegisteredException:
            logger.warning(f"{event_dict['type']} is not a registered reminder.")
        except Exception as error:
            logger.error(f"Sending reminder error: {error}")


def get_timezones() -> dict:
    """
    Emit event that collects all enabled users with their timezones.
    @return: User timezones dict {<userId>: <timezone>}
    """
    event_bus = inject.instance(EventBusAdapter)
    results = event_bus.emit(RequestUsersTimezonesEvent())
    if not results:
        raise Exception("No data returned from RequestUsersTimezonesEvent")
    users_timezones = {}
    for result in results:
        if not isinstance(result, dict):
            logger.error(f"Expected type dict, got {type(result)}")
            continue
        users_timezones.update(result)
    return users_timezones
