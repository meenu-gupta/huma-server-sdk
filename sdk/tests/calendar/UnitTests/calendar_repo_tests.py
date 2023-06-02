import unittest
from unittest.mock import MagicMock

from bson import ObjectId
from pymongo.database import Database

from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.repo.mongo_calendar_repository import (
    MongoCalendarRepository,
    to_mongo_calendar_event,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject

USER_ID = "600a8476a961574fb38157d5"


class CalendarRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

        def bind(binder):
            binder.bind(Database, self.db)

        inject.clear_and_configure(bind)

    class TestEvent(CalendarEvent):
        def pack_extra_fields(self):
            pass

    def test_success_delete_calendar_on_user_delete(self):
        session = MagicMock()
        repo = MongoCalendarRepository()
        repo.delete_user_events(user_id=USER_ID, session=session)
        user_id = ObjectId(USER_ID)
        self.db[repo.CALENDAR_COLLECTION].delete_many.assert_called_with(
            {CalendarEvent.USER_ID: user_id}, session=session
        )
        self.db[repo.CACHE_CALENDAR_COLLECTION].delete_many.assert_called_with(
            {CalendarEvent.USER_ID: user_id}, session=session
        )

    @staticmethod
    def _sample_event_dict() -> dict:
        return {
            CalendarEvent.ID: str(ObjectId()),
            CalendarEvent.MODEL: "TestEvent",
            CalendarEvent.COMPLETE_DATE_TIME: "2020-10-20T20:20:20.000Z",
        }

    def test_to_mongo_calendar_event(self):
        CalendarEvent.register(self.TestEvent.__name__, self.TestEvent)
        event_dict = self._sample_event_dict()
        event = CalendarEvent.from_dict(event_dict)
        mongo_event = to_mongo_calendar_event(event)
        self.assertEqual(event.id, str(mongo_event.id))

    def test_failure_update_event_wrong_id(self):
        CalendarEvent.register(self.TestEvent.__name__, self.TestEvent)
        repo = MongoCalendarRepository()
        event_dict = self._sample_event_dict()
        event = CalendarEvent.from_dict(event_dict)
        with self.assertRaises(InvalidRequestException):
            repo.update_calendar_event("invalid_id", event)


if __name__ == "__main__":
    unittest.main()
