from datetime import datetime, timedelta
from unittest import TestCase

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrulestr
from freezegun import freeze_time

from extensions.authorization.models.user import User
from extensions.deployment.models.key_action_config import (
    KeyActionConfig,
    validate_duration_iso,
)
from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from extensions.key_action.models.key_action_log import KeyAction
from extensions.tests.authorization.IntegrationTests.test_helpers import DEPLOYMENT_ID
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.utils import no_seconds


class KeyActionConfigTestCase(TestCase):
    def setUp(self) -> None:
        self.now = datetime.utcnow()
        self.key_action_hour = self.now.hour - 1
        self.key_action_minute = self.now.minute
        CalendarEvent.register(KeyAction.__name__, KeyAction)

    def key_action_config(self, delta_from_trigger):
        config_dict = {
            "id": "611dfe2b5f627d7d824c297a",
            "durationFromTrigger": "P2W",
            "deltaFromTriggerTime": delta_from_trigger,
            "durationIso": f"P1WT{self.key_action_hour}H{self.key_action_minute}M",
            "type": "LEARN",
            "trigger": "SURGERY",
            "learnArticleId": "611dfe2b5f627d7d824c297a",
        }
        return KeyActionConfig.from_dict(config_dict)

    def test_build_key_action_event_delta_P1D_after_key_action_trigger(self):
        with freeze_time(self.now):
            hour = self.now.hour - 1
            minute = self.now.minute
            user = User(id="611dfe2b5f627d7d824c297a", timezone="UTC")
            generator = KeyActionGenerator(user, self.now, DEPLOYMENT_ID)
            key_action: KeyAction = generator.build_key_action_from_config(
                config=self.key_action_config("P1D")
            )

            # should be next day as delta from trigger is P1D
            expected_time = (self.now + relativedelta(days=1)).replace(
                hour=hour, minute=minute
            )
            r_rule = rrulestr(key_action.recurrencePattern)
            self.assertEqual(no_seconds(expected_time), r_rule._dtstart)

    def test_build_key_action_event_delta_P0D_before_key_action_trigger(self):
        with freeze_time(self.now):
            user = User(id="611dfe2b5f627d7d824c297a", timezone="UTC")
            generator = KeyActionGenerator(
                user, self.now - timedelta(hours=2), DEPLOYMENT_ID
            )
            key_action: KeyAction = generator.build_key_action_from_config(
                config=self.key_action_config("P0D")
            )

            # should be this day
            expected_time = self.now.replace(
                hour=self.key_action_hour, minute=self.key_action_minute
            )
            r_rule = rrulestr(key_action.recurrencePattern)
            self.assertEqual(no_seconds(expected_time), r_rule._dtstart)

    def test_success_validate_duration_iso(self):
        valid_durations = ["P6YT1H1M", "P6MT1H1M", "P6DT1H1M", "P6WT1H1M"]
        for duration in valid_durations:
            res = validate_duration_iso(duration)
            self.assertTrue(res)

    def test_failure_validate_duration_iso_double_duration(self):
        duration = "P6Y5MT1H1M"
        with self.assertRaises(Exception):
            validate_duration_iso(duration)
