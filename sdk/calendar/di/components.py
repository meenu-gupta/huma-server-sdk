import logging

from sdk.calendar.repo.calendar_repository import CalendarRepository
from sdk.calendar.repo.mongo_calendar_repository import MongoCalendarRepository


logger = logging.getLogger(__name__)


def bind_calendar_repository(binder, config):
    binder.bind_to_provider(CalendarRepository, lambda: MongoCalendarRepository())
    logger.debug("CalendarRepository bind to MongoCalendarRepository")
