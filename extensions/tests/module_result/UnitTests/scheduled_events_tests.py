from unittest import TestCase
from unittest.mock import MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.module_result.models.module_config import (
    ModuleConfig,
    NotificationData,
    CustomModuleConfig,
    ModuleSchedule,
    Weekday,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from extensions.module_result.models.scheduled_event_utils import to_scheduled_events
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.utils.convertible import ConvertibleClassValidationError


MODULE_CONFIG_ID = "5d386cc6ff885918d96adb2c"


class ModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        CalendarEvent.register(ScheduledEvent.__name__, ScheduledEvent)

    def test_success_create(self):
        data = {
            ScheduledEvent.MODEL: ScheduledEvent.__name__,
            ScheduledEvent.MODULE_ID: "Temperature",
            ScheduledEvent.MODULE_CONFIG_ID: MODULE_CONFIG_ID,
        }
        try:
            ScheduledEvent.from_dict(data)
        except Exception as error:
            self.fail(str(error))

    def test_failure_missing_required_fields(self):
        data = {
            ScheduledEvent.MODEL: ScheduledEvent.__name__,
            ScheduledEvent.MODULE_CONFIG_ID: MODULE_CONFIG_ID,
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ScheduledEvent.from_dict(data)

        data = {
            ScheduledEvent.MODEL: ScheduledEvent.__name__,
            ScheduledEvent.MODULE_ID: "Temperature",
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ScheduledEvent.from_dict(data)

    def test_set_default_title_and_description(self):
        authz_user = MagicMock()
        authz_user.deployment = self._deployment()
        authz_user.get_language.return_value = "en"
        event = ScheduledEvent(moduleId="Temperature", moduleConfigId=MODULE_CONFIG_ID)
        event.set_default_title_and_description(authz_user)
        self.assertEqual("Test title", event.title)
        self.assertEqual("Test body", event.description)

    @staticmethod
    def _deployment():
        return Deployment(
            moduleConfigs=[
                ModuleConfig(
                    id=MODULE_CONFIG_ID,
                    moduleId="Temperature",
                    notificationData=NotificationData(
                        title="Test title",
                        body="Test body",
                    ),
                )
            ]
        )


class ScheduledEventUtilsTestCase(TestCase):
    def test_to_scheduled_events(self):
        config = CustomModuleConfig(
            schedule=ModuleSchedule(
                isoDuration="P1W",
                specificWeekDays=[Weekday.TUE, Weekday.FRI],
                timesOfReadings=["PT10H30M", "PT18H0M"],
            ),
        )
        events = to_scheduled_events(config, "UTC")
        self.assertEqual(2, len(events))

        expected_pattern = (
            "RRULE:FREQ=WEEKLY;BYDAY=TU,FR;BYHOUR=10;BYMINUTE=30;BYSECOND=0"
        )
        self.assertIn(expected_pattern, events[0].recurrencePattern)
        # expires when next event starts
        self.assertEqual("PT450M", events[0].instanceExpiresIn)

        expected_pattern = (
            "RRULE:FREQ=WEEKLY;BYDAY=TU,FR;BYHOUR=18;BYMINUTE=0;BYSECOND=0"
        )
        self.assertIn(expected_pattern, events[1].recurrencePattern)
        # expires when next event starts
        self.assertEqual("PT990M", events[1].instanceExpiresIn)

    def test_module_schedule_sorting(self):
        data = {
            ModuleSchedule.ISO_DURATION: "P1W",
            ModuleSchedule.TIMES_OF_READINGS: ["PT15H10M", "PT10H0M"],
            ModuleSchedule.SPECIFIC_WEEK_DAYS: ["FRI", "MON"],
        }
        schedule: ModuleSchedule = ModuleSchedule.from_dict(data)
        self.assertEqual("PT10H0M", schedule.timesOfReadings[0])
        self.assertEqual(Weekday.MON, schedule.specificWeekDays[0])
