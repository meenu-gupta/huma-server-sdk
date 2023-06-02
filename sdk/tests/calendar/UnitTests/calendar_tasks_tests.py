import unittest
from unittest.mock import patch, MagicMock

from celery.schedules import crontab

from sdk.calendar.tasks import (
    setup_periodic_tasks,
    prepare_events_for_next_day,
    prepare_events_and_execute,
    event_to_typed_dict,
)

CALENDAR_TASKS_PATH = "sdk.calendar.tasks"


class CalendarTasksTestCase(unittest.TestCase):
    @patch(f"{CALENDAR_TASKS_PATH}.celery_app", MagicMock())
    @patch(f"{CALENDAR_TASKS_PATH}.prepare_events_for_next_day")
    def test_success_setup_periodic_tasks(self, prepare_events):
        sender = MagicMock()
        setup_periodic_tasks(sender)
        sender.add_periodic_task.assert_called_with(
            crontab(hour=3, minute=0), prepare_events.s(), name="New users handler"
        )

    @patch(f"{CALENDAR_TASKS_PATH}.CalendarService")
    @patch(f"{CALENDAR_TASKS_PATH}.get_timezones")
    def test_success_prepare_events_for_next_day(self, get_timezones, service):
        prepare_events_for_next_day()
        service().calculate_and_save_next_day_events.assert_called_with(get_timezones())

    @patch(f"{CALENDAR_TASKS_PATH}.CalendarService")
    @patch(f"{CALENDAR_TASKS_PATH}.now_no_seconds")
    def test_success_prepare_events_and_execute(self, now_no_seconds, service):
        prepare_events_and_execute()
        service().retrieve_next_day_events.assert_called_with(
            {"startDateTime": now_no_seconds()}
        )
        service().batch_delete_next_day_events.assert_called_with([])

    def test_success_event_to_typed_dict(self):
        event = MagicMock()
        res = event_to_typed_dict(event)
        self.assertTrue(isinstance(res, dict))
        self.assertIn("type", res)


if __name__ == "__main__":
    unittest.main()
