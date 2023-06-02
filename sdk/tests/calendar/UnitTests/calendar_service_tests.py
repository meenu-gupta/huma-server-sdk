import unittest
from unittest.mock import MagicMock, patch

import pytz
from freezegun import freeze_time

from sdk.calendar.models.calendar_event import CalendarEvent as Event
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.utils.validators import utc_str_val_to_field

TEST_PATTERN = "DTSTART:20210101T100000\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20210105T100000;BYHOUR=10;BYMINUTE=0"
SAMPLE_ID = "61c56b6b64d0f5b742c4b897"


class CalendarRepoMock:
    instance = MagicMock()
    retrieve_calendar_event_logs = MagicMock()
    create_next_day_events = MagicMock()


class EventBusMock:
    instance = MagicMock()


class EventMock:
    instance = MagicMock()
    instanceExpiresIn = "expires_in_data"
    description = "description_data"
    enabled = True


class TestEvent(Event):
    def pack_extra_fields(self):
        pass

    def execute(self, run_async=True):
        pass


class CalendarServiceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Event.register(TestEvent.__name__, TestEvent)

    def setUp(self) -> None:
        self.repo = CalendarRepoMock()
        self.repo.create_next_day_events.reset_mock()
        self.service = CalendarService(repo=self.repo, event_bus=EventBusMock())
        self.service.retrieve_calendar_event_logs = MagicMock()

    def _get_calendar_event(self, enabled=True) -> Event:
        data = {
            Event.ID: SAMPLE_ID,
            Event.IS_RECURRING: True,
            Event.RECURRENCE_PATTERN: TEST_PATTERN,
            Event.SNOOZING: ["PT10M", "PT20M"],
            Event.MODEL: TestEvent.__name__,
            Event.PARENT_ID: SAMPLE_ID,
            Event.ENABLED: enabled,
        }
        return Event.from_dict(data)

    def test_success_set_event_description_debug(self):
        rows_in_response = [
            "Event Description: description_data",
            "Instance Expires In: expires_in_data",
        ]
        res = self.service._set_event_description(EventMock(), debug=True)
        for row in rows_in_response:
            self.assertIn(row, res)

    def test_success_set_event_description_no_debug(self):
        event = EventMock()
        res = self.service._set_event_description(event)
        self.assertEqual("description_data", res)

    @freeze_time("2021-01-01T10:00:00.000Z")
    def test_create_next_day_event(self):
        event = self._get_calendar_event()
        self.service.create_next_day_event(event, "UTC")
        self.repo.create_next_day_events.assert_called_once()
        events = self.repo.create_next_day_events.call_args.args[0]
        self.assertEqual(3, len(events))

    @freeze_time("2021-01-01T10:00:00.000Z")
    def test_create_next_day_event_not_called_for_disabled_event(self):
        event = self._get_calendar_event(enabled=False)
        self.service.create_next_day_event(event, "UTC")
        self.repo.create_next_day_events.assert_not_called()

    @freeze_time("2021-01-05T10:00:00.000Z")
    def test_calculate_and_save_next_day_events_for_user_no_events(self):
        repo = MagicMock()
        repo.retrieve_calendar_events().return_value = []
        service = CalendarService(repo, None)
        service.save_next_day_events = MagicMock()

        service.calculate_and_save_next_day_events_for_user("testUser", "UTC")
        service.save_next_day_events.assert_not_called()

    @freeze_time("2021-01-05T10:00:00.000Z")
    def test_calculate_and_save_next_day_events_for_user(self):
        repo = MagicMock()
        event = TestEvent(
            id=SAMPLE_ID,
            userId=SAMPLE_ID,
            model=TestEvent.__name__,
            isRecurring=True,
            startDateTime="2021-01-01T12:00:00.000000Z",
            recurrencePattern=TEST_PATTERN,
        )
        repo.retrieve_calendar_events.return_value = [event]
        service = CalendarService(repo, None)
        service.save_next_day_events = MagicMock()

        service.calculate_and_save_next_day_events_for_user(SAMPLE_ID, "UTC")
        expected_value = TestEvent(
            userId=SAMPLE_ID,
            model=event.model,
            isRecurring=False,
            # freeze time is 2021-01-05 at 10am UTC according to TEST_PATTERN
            startDateTime="2021-01-05T10:00:00.000000Z",
            parentId=event.id,
            endDateTime="2021-01-12T09:59:00.000000Z",
        )
        service.save_next_day_events.assert_called_with([expected_value])

    @freeze_time("2021-01-05T10:00:00.000Z")
    def test_calculate_and_save_next_day_events(self):
        repo = MagicMock()
        event = TestEvent(
            id=SAMPLE_ID,
            userId=SAMPLE_ID,
            model=TestEvent.__name__,
            isRecurring=True,
            startDateTime="2021-01-01T12:00:00.000000Z",
            recurrencePattern=TEST_PATTERN,
        )
        repo.retrieve_calendar_events.return_value = [event]
        service = CalendarService(repo, None)
        service.save_next_day_events = MagicMock()

        service.calculate_and_save_next_day_events({SAMPLE_ID: "UTC"})
        expected_value = TestEvent(
            userId=SAMPLE_ID,
            model=event.model,
            isRecurring=False,
            # freeze time is 2021-01-05 at 10am UTC according to TEST_PATTERN
            startDateTime="2021-01-05T10:00:00.000000Z",
            parentId=event.id,
            endDateTime="2021-01-12T09:59:00.000000Z",
        )
        service.save_next_day_events.assert_called_with([expected_value])

    @freeze_time("2021-01-05T10:00:00.000Z")
    @patch(
        "sdk.calendar.service.calendar_service.CalendarService.batch_delete_calendar_events_by_ids"
    )
    def test_calculate_and_save_next_day_events__remove_events_with_no_user_found(
        self, batch_delete
    ):
        repo = MagicMock()
        calendar_id = SAMPLE_ID
        event = TestEvent(
            id=calendar_id,
            userId=SAMPLE_ID,
            model=TestEvent.__name__,
            isRecurring=True,
            startDateTime="2021-01-01T12:00:00.000000Z",
            recurrencePattern=TEST_PATTERN,
        )
        repo.retrieve_calendar_events.return_value = [event]
        service = CalendarService(repo, None)
        service.save_next_day_events = MagicMock()

        service.calculate_and_save_next_day_events({"wrong_user_id": pytz.UTC})
        batch_delete.assert_called_with([calendar_id])
