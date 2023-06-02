import random
from datetime import timedelta
from unittest import TestCase

import pytz
from bson import ObjectId
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from sdk.calendar.models.calendar_event import CalendarEvent, CalendarEventLog
from sdk.calendar.utils import get_dt_from_str
from sdk.common.utils.convertible import ConvertibleClassValidationError


class CalendarEventTestCase(TestCase):
    def setUp(self) -> None:
        CalendarEvent.register(CalendarEvent.__name__, CalendarEvent)

    def test_as_timezone(self):
        end = "2021-03-01T13:09:00.000Z"
        # create event that triggers once
        rule = "DTSTART:20210201T020000\nRRULE:FREQ=WEEKLY;INTERVAL=10;UNTIL=20210301T130900;BYHOUR=10;BYMINUTE=0"
        calendar_event_dict = {
            CalendarEvent.RECURRENCE_PATTERN: rule,
            CalendarEvent.MODEL: "CalendarEvent",
            CalendarEvent.END_DATE_TIME: end,
        }
        end_date = get_dt_from_str(end)
        for timezone_name in random.choices(pytz.all_timezones, k=5):
            with freeze_time(end_date - relativedelta(days=15)):
                event: CalendarEvent = CalendarEvent.from_dict(calendar_event_dict)
                event.as_timezone(pytz.timezone(timezone_name))
                r_rule = rrule.rrulestr(event.recurrencePattern)
                self.assertEqual(1, len(list(r_rule)), timezone_name)

    def test_calendar_log_as_timezone(self):
        test_cases = (
            ("UTC", timedelta(hours=0)),
            ("Europe/Kiev", timedelta(hours=2)),
            ("Asia/Kolkata", timedelta(hours=5, minutes=30)),
        )
        start = get_dt_from_str("2021-01-01T10:00:00.000Z")
        end = get_dt_from_str("2021-01-08T10:00:00.000Z")

        for timezone, delta in test_cases:
            tz = pytz.timezone(timezone)
            log = CalendarEventLog(startDateTime=start, endDateTime=end)
            log.as_timezone(tz)

            self.assertEqual(delta, start - log.startDateTime)
            self.assertEqual(delta, end - log.endDateTime)

    @staticmethod
    def _sample_calendar_event_dict() -> dict:
        return {
            CalendarEvent.ID: str(ObjectId()),
            CalendarEvent.MODEL: "CalendarEvent",
            CalendarEvent.COMPLETE_DATE_TIME: "2020-10-20T20:20:20.000Z",
            CalendarEvent.USER_ID: str(ObjectId()),
        }

    def test_calendar_event_user_id_should_be_valid_object_id(self):
        event_dict = self._sample_calendar_event_dict()
        try:
            CalendarEvent.from_dict(event_dict)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_calendar_event__user_id_is_not_valid(self):
        event_dict = self._sample_calendar_event_dict()
        event_dict[
            CalendarEvent.USER_ID
        ] = "io.restassured.internal.NoParameterValue@27ddc4d3"
        with self.assertRaises(ConvertibleClassValidationError):
            CalendarEvent.from_dict(event_dict)
