from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import isodate
import pytz
from bson import ObjectId
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, MONTHLY
from freezegun import freeze_time

from extensions.appointment.component import AppointmentComponent
from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.router.user_profile_request import (
    LinkProxyRequestObject,
    UpdateUserProfileRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.key_action.callbacks.key_action_generator import KeyActionGenerator
from extensions.key_action.component import KeyActionComponent
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.reminder.component import UserModuleReminderComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.auth.use_case.auth_request_objects import SignUpRequestObject
from sdk.calendar.component import CalendarComponent
from sdk.calendar.models.mongo_calendar_event import MongoCalendarEvent
from sdk.calendar.repo.mongo_calendar_repository import MongoCalendarRepository
from sdk.calendar.tasks import (
    prepare_events_and_execute,
    prepare_events_for_next_day,
)
from sdk.calendar.utils import no_seconds
from sdk.celery.app import celery_app
from sdk.common.utils.validators import utc_str_field_to_val
from sdk.notification.component import NotificationComponent
from sdk.notification.services.notification_service import NotificationService
from sdk.versioning.component import VersionComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789a"
VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
VALID_KEY_ACTION_ID = "5f0f0373d656ed903e5a969e"
SEND_NOTIFICATION_ROUTE = (
    "extensions.appointment.models.appointment_event.AppointmentEvent.execute"
)
PROXY_EMAIL = "proxy@test.com"


def nearest_weekday_date(date_obj, day):
    # Returns the date of the next given weekday (starting from 0 for Monday)
    # after the given date. For example, the date of next Monday.
    # NB: if it IS the day we're looking for, this returns same date.
    return date_obj + relativedelta(days=(day - date_obj.weekday() + 7) % 7)


def get_sample_appointment_data(uid: str, now_time):
    return {
        "userId": uid,
        "startDateTime": (now_time + relativedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
    }


class CalendarTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        CalendarComponent(),
        ModuleResultComponent(),
        KeyActionComponent(),
        UserModuleReminderComponent(),
        AppointmentComponent(),
        OrganizationComponent(),
        NotificationComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    DURATION_FROM_TRIGGER = "P6M"
    NOTIFY_EVERY = "PT5M"
    NOTIFICATIONS_AMOUNT = 3
    DEFAULT_DURATION_DAYS = 10
    DEFAULT_EXPIRATION_DAYS = 7

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(VALID_USER_ID)

        self.now = datetime.utcnow()
        self.hour_ahead = self.now + relativedelta(hours=1)
        self.hour_behind = self.now - relativedelta(hours=1)
        self.half_hour_ahead = self.now + relativedelta(minutes=30)
        self.half_hour_behind = self.now - relativedelta(minutes=30)
        self.few_minutes = relativedelta(minutes=10)
        self.uid = VALID_USER_ID

    def _refresh_headers(self, uid=None):
        uid = uid if uid else self.uid
        self.headers = self.get_headers_for_token(uid)

    def _configure_key_action(
        self,
        custom_delta: int = None,
        custom_duration_days: int = None,
        expire_in_days: int = None,
        custom_duration_str: str = None,
        trigger_delay: str = None,
    ):
        # the configuration is for 1 hour ahead by default
        service = DeploymentService()
        delta = custom_delta if custom_delta is not None else 1
        key_action_time = self.now + relativedelta(hours=delta)
        hour = key_action_time.hour
        minute = key_action_time.minute
        if not custom_duration_str:
            duration_days = (
                self.DEFAULT_DURATION_DAYS
                if not custom_duration_days
                else custom_duration_days
            )
            duration_str = f"P{duration_days}DT{hour}H{minute}M"
        else:
            duration_str = custom_duration_str

        expires_in = f"P{expire_in_days or self.DEFAULT_EXPIRATION_DAYS}D"
        key_action_cfg = KeyActionConfig.from_dict(
            {
                "title": "Blood Pressure",
                "description": "Time to measure your blood pressure",
                "deltaFromTriggerTime": trigger_delay or "PT0M",
                "durationFromTrigger": self.DURATION_FROM_TRIGGER,
                "type": "MODULE",
                "trigger": "SIGN_UP",
                "durationIso": duration_str,
                "numberOfNotifications": self.NOTIFICATIONS_AMOUNT,
                "notifyEvery": self.NOTIFY_EVERY,
                "moduleId": "BloodPressure",
                "moduleConfigId": "5ee836d9ba9fd528807029bc",
                "instanceExpiresIn": expires_in,
            }
        )
        service.create_key_action(
            deployment_id=VALID_DEPLOYMENT_ID, key_action=key_action_cfg
        )

    @staticmethod
    def _sample_user(tz="UTC"):
        return {
            SignUpRequestObject.METHOD: 1,
            SignUpRequestObject.PHONE_NUMBER: "+447475768333",
            SignUpRequestObject.EMAIL: "user@test.com",
            SignUpRequestObject.DISPLAY_NAME: "test",
            SignUpRequestObject.VALIDATION_DATA: {"activationCode": "53924415"},
            SignUpRequestObject.USER_ATTRIBUTES: {
                "familyName": "hey",
                "givenName": "test",
                "dob": "1988-02-20",
                "gender": "MALE",
            },
            SignUpRequestObject.CLIENT_ID: "ctest1",
            SignUpRequestObject.PROJECT_ID: "ptest1",
            SignUpRequestObject.TIMEZONE: tz,
        }

    def _sample_manager(self, tz="UTC"):
        return {
            **self._sample_user(),
            SignUpRequestObject.PHONE_NUMBER: "+447475768334",
            SignUpRequestObject.EMAIL: "manager@test.com",
            SignUpRequestObject.DISPLAY_NAME: "managerTest",
            SignUpRequestObject.VALIDATION_DATA: {"activationCode": "17781957"},
            SignUpRequestObject.TIMEZONE: tz,
        }

    def _sample_proxy(self, activation_code):
        return {
            **self._sample_user(),
            SignUpRequestObject.PHONE_NUMBER: "+447475768335",
            SignUpRequestObject.EMAIL: PROXY_EMAIL,
            SignUpRequestObject.DISPLAY_NAME: "proxy",
            SignUpRequestObject.VALIDATION_DATA: {
                "activationCode": activation_code or "53924416"
            },
        }

    def _sign_up_user(self, manager=False, tz="UTC"):
        data = self._sample_manager(tz) if manager else self._sample_user(tz)
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        return rsp.json["uid"]

    def _sign_up_proxy(self, activation_code: str = None):
        data = self._sample_proxy(activation_code)
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        return rsp.json["uid"]

    def _sign_up_proxy_and_link(self, user_id: str, activation_code: str = None):
        proxy_id = self._sign_up_proxy(activation_code)
        user_headers = self.get_headers_for_token(user_id)
        link_data = {LinkProxyRequestObject.PROXY_EMAIL: PROXY_EMAIL}
        with patch.object(NotificationService, "push_for_user"):
            self.flask_client.post(
                f"/api/extensions/v1beta/user/{user_id}/assign-proxy",
                json=link_data,
                headers=user_headers,
            )
        return proxy_id

    def _key_actions_request(self, uid):
        user_key_actions_url = f"/api/extensions/v1beta/user/{uid}/key-action"
        self.headers = self.get_headers_for_token(uid)
        rsp = self.flask_client.get(user_key_actions_url, headers=self.headers)
        return rsp

    def _send_blood_pressure_data(self, uid):
        module_result = [
            {
                "type": "BloodPressure",
                "deviceName": "iOS",
                "deploymentId": VALID_DEPLOYMENT_ID,
                "startDateTime": utc_str_field_to_val(self.now),
                "diastolicValue": 80,
                "systolicValue": 100,
            }
        ]
        self.headers = self.get_headers_for_token(uid)
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{uid}/module-result/BloodPressure",
            json=module_result,
            headers=self.headers,
        )
        return rsp


class KeyActionCalendarTestCase(CalendarTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(KeyActionCalendarTestCase, cls).setUpClass()
        cls.base_url = f"/api/extensions/v1beta/user/{VALID_USER_ID}/key-action"

    @patch("sdk.calendar.tasks.execute_events")
    def test_sending_sign_up_notifications(self, mock_execute_events):
        with freeze_time(self.hour_behind):
            self._configure_key_action()
        with freeze_time(self.now):
            self._sign_up_user()
        notify_period = isodate.parse_duration(self.NOTIFY_EVERY)
        # generating list of notification deltas with one extra as incorrect delta at the end
        notification_deltas = [
            notify_period * n for n in range(1, self.NOTIFICATIONS_AMOUNT + 2)
        ]
        # popping incorrect delta
        invalid_delta = notification_deltas.pop()

        # checking that each required notification is pushed
        # setting date to required push date, and checking if necessary methods were called

        for delta in notification_deltas:
            with freeze_time(self.hour_ahead + delta):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_called_once()
                self.assertEqual(2, len(mock_execute_events.delay.call_args))
                mock_execute_events.delay.reset_mock()

        # checking that no extra notification pushed
        with freeze_time(self.hour_ahead + invalid_delta):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_not_called()

    def test_key_action_appears_after_sign_up_correctly(self):
        """
        Hour ahead is the moment when key action should appear
        """
        expires_in_days = 3
        with freeze_time(self.hour_behind):
            self._configure_key_action(expire_in_days=expires_in_days)

        with freeze_time(self.now):
            uid = self._sign_up_user()

        with freeze_time(self.hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(self.half_hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 0 key action for user after sign up but before key action time
            self.assertEqual(0, len(rsp.json))

        with freeze_time(self.hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(
            self.hour_ahead + relativedelta(days=expires_in_days, minutes=-1)
        ):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time whole week
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(self.hour_ahead + relativedelta(days=expires_in_days)):
            rsp = self._key_actions_request(uid)
            # confirming key actions reset for user after a week
            self.assertEqual(0, len(rsp.json))

        with freeze_time(
            self.hour_ahead + relativedelta(days=self.DEFAULT_DURATION_DAYS - 1)
        ):
            rsp = self._key_actions_request(uid)
            # confirming we got 0 key actions for user after sign up at key action time the day before new period
            self.assertEqual(0, len(rsp.json))

        next_period_trigger_time = self.hour_ahead + relativedelta(
            days=self.DEFAULT_DURATION_DAYS
        )
        with freeze_time(next_period_trigger_time):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time pn next period
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(
            self.hour_ahead + relativedelta(days=self.DEFAULT_DURATION_DAYS + 1)
        ):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

    def test_success_retrieve_key_action_after_sign_up_after_6M(self):
        """
        Hour ahead is the moment when key action should appear
        """
        with freeze_time(self.hour_behind):
            self._configure_key_action(trigger_delay="P6M")

        with freeze_time(self.now):
            uid = self._sign_up_user()

        with freeze_time(self.now + relativedelta(months=6, hours=1)):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

    def test_key_action_not_duplicated(self):
        with freeze_time(self.hour_behind):
            self._configure_key_action(custom_duration_days=7)

        with freeze_time(self.now):
            uid = self._sign_up_user()

        with freeze_time(self.hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(
            self.hour_ahead + relativedelta(days=7) - relativedelta(minutes=1)
        ):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(self.hour_ahead + relativedelta(days=7)):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        with freeze_time(
            self.hour_ahead + relativedelta(days=7) + relativedelta(minutes=1)
        ):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

    def test_key_action_disappears_after_duration_from_trigger_expires(self):
        with freeze_time(self.hour_behind):
            self._configure_key_action()
        with freeze_time(self.now):
            uid = self._sign_up_user()

        with freeze_time(self.hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up at key action time
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

        # testing if after durationFromTrigger period key actions disappear itself
        trigger_delta = isodate.parse_duration(self.DURATION_FROM_TRIGGER)
        expiration_date = self.hour_ahead + trigger_delta
        with freeze_time(expiration_date):
            # confirming we got 0 key actions after expiration date
            rsp = self._key_actions_request(uid)
            self.assertEqual(0, len(rsp.json))

        with freeze_time(expiration_date - relativedelta(days=1)):
            # checking if we still have key action the day before expiration
            # IMPORTANT NOTE: if test fails at some days, we should calculate correct logic that
            # 1 day before expiration is actually correct day to show the key action
            # as it may be period between 7th day when key action disappears
            # till new period at 10th day
            # UPD: try to swap place trigger delta with relativedelta(days=1)
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

    @patch("sdk.calendar.tasks.execute_events")
    def test_key_action_sent_with_module_result_submitted_before_it(
        self, mock_execute_events
    ):
        """
        Key Action should be sent to user even if result was submitted before key action time
        """
        # 1. Create key action config
        with freeze_time(self.hour_behind):
            self._configure_key_action()
        # 2. Create user
        with freeze_time(self.half_hour_behind):
            uid = self._sign_up_user()
        # 3. Send blood pressure before key action (key action 1 hour after NOW)
        self._send_blood_pressure_data(uid)
        # 4. Check at key action time that user got key action
        with freeze_time(self.hour_ahead):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])
        # 5. Check notification triggered at key action time
        with freeze_time(self.hour_ahead):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            self.assertEqual(2, len(mock_execute_events.delay.call_args))
            mock_execute_events.delay.reset_mock()

    @patch("sdk.calendar.tasks.execute_events", MagicMock())
    def test_key_action_disappears_after_module_result_submitted(self):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.half_hour_behind):
            uid = self._sign_up_user()
        # 3. Check at key action time that user got key action
        with freeze_time(self.now):
            rsp = self._key_actions_request(uid)
            # confirming we got 1 key action for user after sign up
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])
        # 4. Send module data after key action appeared and check that it disappeared
        self._send_blood_pressure_data(uid)
        # 5. Check no key action after data is pushed
        with freeze_time(self.now + relativedelta(minutes=1)):
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            # here we got key action but its disabled
            self.assertFalse(rsp.json[0]["enabled"])

        # 6. Check no key action after changing timezone
        self.mongo_database["user"].update_one(
            {"_id": ObjectId(uid)}, {"$set": {User.TIMEZONE: "Europe/Kiev"}}
        )
        with freeze_time(self.now + relativedelta(minutes=1)):
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            # here we got key action but its disabled
            self.assertFalse(rsp.json[0]["enabled"])

    @patch("sdk.calendar.tasks.execute_events")
    def test_notification_sent_correctly(self, mock_execute_events):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.half_hour_behind):
            self._sign_up_user()
        # 3. Check notification triggered at key action time
        with freeze_time(self.now):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            self.assertEqual(2, len(mock_execute_events.delay.call_args))

    def test_success_creation_with_yearly_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P2YT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_success_creation_with_monthly_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P6MT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_success_creation_with_weekly_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P6WT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_success_creation_with_daily_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P6DT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_success_creation_with_monthly_float_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P1.5MT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_success_creation_with_yearly_float_duration(self):
        events_before = self.mongo_database["calendar"].find({}).count()
        self._configure_key_action(custom_duration_str="P1.5YT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(2, events_after)
        self.assertNotEqual(events_before, events_after)

    def test_not_created_with_0_in_date(self):
        self._configure_key_action(custom_duration_str="P0DT1H1M")
        self._sign_up_user()
        events_after = self.mongo_database["calendar"].find({}).count()
        self.assertEqual(0, events_after)

    def test_fail_creation_with_double_date(self):
        with self.assertRaises(Exception) as context:
            self._configure_key_action(custom_duration_str="P1W1DT1H1M")
        self.assertTrue("Not allowed to use double duration" in str(context.exception))

    @patch("sdk.calendar.tasks.execute_events")
    def test_snoozing_notification_sent_correctly(self, mock_execute_events):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.half_hour_behind):
            uid = self._sign_up_user()
        # 3. Confirming at key action time that key action is shown and enabled
        with freeze_time(self.now):
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])
        # 4. Sending module data after key action appeared and check that it disappeared
        self._send_blood_pressure_data(uid)
        # 5. Check no notifications sent at key action notification time (notifyEvery periods)
        # after data is pushed

        # preparing snoozing deltas with one extra not valid
        snoozing_deltas = KeyActionGenerator.build_snoozing(
            self.NOTIFY_EVERY, self.NOTIFICATIONS_AMOUNT + 1
        )
        for delta in snoozing_deltas:
            with freeze_time(self.now + isodate.parse_duration(delta)):
                rsp = self._key_actions_request(uid)
                # confirming we got 0 key actions for user after sending blood pressure
                self.assertEqual(1, len(rsp.json))
                self.assertFalse(rsp.json[0]["enabled"])
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_not_called()

    def test_key_action_correct_tz_schedule(self):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(days=1, hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user half an hour before now
        signup_time = self.now - relativedelta(hours=1)
        with freeze_time(signup_time):
            uid = self._sign_up_user()
            rsp = self._key_actions_request(uid)
            # 0 key actions at sign up moment
            self.assertEqual(0, len(rsp.json))

            # changing timezone to Kiev and checking that KA is shown as for user its already after KA time
            auth_service = AuthorizationService()
            auth_service.update_user_profile(
                UpdateUserProfileRequestObject(id=uid, timezone="Europe/Kiev")
            )
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])

            # changing timezone to US and checking that KA is not shown as its pre KA time in user's TZ
            auth_service = AuthorizationService()
            auth_service.update_user_profile(
                UpdateUserProfileRequestObject(id=uid, timezone="America/New_York")
            )
            rsp = self._key_actions_request(uid)
            self.assertEqual(0, len(rsp.json))

        # 3. Confirming at key action time by user's TZ that key action is shown
        us_tz = pytz.timezone("America/New_York")
        us_offset = us_tz.utcoffset(signup_time)
        with freeze_time(self.now - us_offset):
            rsp = self._key_actions_request(uid)
            self.assertEqual(1, len(rsp.json))
            self.assertTrue(rsp.json[0]["enabled"])
        # 4. Confirming at key action time by user's TZ that key action is not shown 1 minute before KA time
        with freeze_time(self.now - us_offset - relativedelta(minutes=1)):
            rsp = self._key_actions_request(uid)
            self.assertEqual(0, len(rsp.json))

        # 5. Confirming at key action time that key action is not shown for user as tz is different
        with freeze_time(self.now):
            rsp = self._key_actions_request(uid)
            self.assertEqual(0, len(rsp.json))

    @patch("sdk.calendar.tasks.execute_events")
    def test_notification_not_sent_after_expiration(self, mock_execute_events):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.now):
            self._sign_up_user()
        # 3. Check notification triggered at key action time last which it should actually launch before expire
        expiration_date = self.now + isodate.parse_duration(self.DURATION_FROM_TRIGGER)
        # default KA duration is 10 days, so generating dates with interval of 10 days, with extra expired date
        dates = list(
            rrule(
                freq=DAILY,
                interval=self.DEFAULT_DURATION_DAYS,
                dtstart=self.now,
                until=expiration_date + relativedelta(days=self.DEFAULT_DURATION_DAYS),
            )
        )
        last_correct_date = dates[-2]
        expired_date = dates[-1]
        just_before_last_correct_date = last_correct_date - self.few_minutes
        with freeze_time(just_before_last_correct_date):
            prepare_events_for_next_day.apply()
        with freeze_time(last_correct_date):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            mock_execute_events.delay.reset_mock()
        # 4. Check notification not triggered after key action expired

        with freeze_time(expired_date):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_not_called()
            mock_execute_events.delay.reset_mock()

    def test_notification_duplicated_to_proxy(self):
        celery_app.conf.task_always_eager = True
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.hour_behind):
            user_id = self._sign_up_user()
        # 3. Create proxy user
        with freeze_time(self.half_hour_behind):
            proxy_id = self._sign_up_proxy_and_link(user_id)
        # 4. Check notification triggered at key action time
        with freeze_time(self.now):
            with patch.object(NotificationService, "push_for_user") as mocked_push:
                prepare_events_and_execute.apply()
            notifications_to_send = mocked_push.call_args_list
            self.assertEqual(2, len(notifications_to_send))
            notification_1 = notifications_to_send[0]
            notification_2 = notifications_to_send[1]
            self.assertEqual(user_id, notification_1.args[0])
            self.assertEqual(proxy_id, notification_2.args[0])

    def test_recalculate_events_when_user_changed_role_to_proxy(self):
        calendar_collections = [
            MongoCalendarRepository.CALENDAR_COLLECTION,
            MongoCalendarRepository.CACHE_CALENDAR_COLLECTION,
        ]
        celery_app.conf.task_always_eager = True
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)

        # 2. Create user
        with freeze_time(self.hour_behind):
            user_id = self._sign_up_user()

        for collection in calendar_collections:
            res = self.mongo_database[collection].find(
                {MongoCalendarEvent.USER_ID: ObjectId(user_id)}
            )
            self.assertTrue(len([i for i in res]))

        manager_headers = self.get_headers_for_token(VALID_MANAGER_ID)
        role = RoleAssignment.create_role(RoleName.PROXY, VALID_DEPLOYMENT_ID)
        path = "/api/extensions/v1beta/user"
        rsp = self.flask_client.post(
            f"{path}/{user_id}/add-role",
            json=[role.to_dict()],
            headers=manager_headers,
        )
        self.assertEqual(rsp.status_code, 200)

        for collection in calendar_collections:
            res = self.mongo_database[collection].find(
                {MongoCalendarEvent.USER_ID: ObjectId(user_id)}
            )
            self.assertFalse(len([i for i in res]))

    def test_no_key_actions_for_proxy_at_signup(self):
        celery_app.conf.task_always_eager = True
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.hour_behind):
            self._sign_up_proxy()
        # 3. Check notification not triggered at key action time
        with freeze_time(self.now):
            with patch.object(NotificationService, "push_for_user") as mocked_push:
                prepare_events_and_execute.apply()
            mocked_push.assert_not_called()

    def test_key_action_completed_for_user_after_proxy_submission(self):
        # 1. Create key action config
        with freeze_time(self.now - relativedelta(hours=2)):
            # generating key action to run at NOW
            self._configure_key_action(custom_delta=0)
        # 2. Create user
        with freeze_time(self.hour_behind):
            user_id = self._sign_up_user(tz="Europe/Kiev")
        # 3. Create proxy user
        with freeze_time(self.half_hour_behind):
            proxy_id = self._sign_up_proxy_and_link(user_id)
        # 4. Check notification triggered at key action time
        with freeze_time(self.now + relativedelta(days=1)):
            url = self.base_url.replace(VALID_USER_ID, user_id)
            headers = self.get_headers_for_token(proxy_id)
            rsp = self.flask_client.get(url, headers=headers)
            key_action = rsp.json[0]

            # create key action log by proxy
            log_url = f"{url}/{key_action['id']}"
            data = {
                KeyAction.START_DATE_TIME: key_action[KeyAction.START_DATE_TIME],
                KeyAction.END_DATE_TIME: key_action[KeyAction.END_DATE_TIME],
                KeyAction.MODEL: key_action[KeyAction.MODEL],
            }
            rsp = self.flask_client.post(log_url, json=data, headers=headers)
            self.assertEqual(201, rsp.status_code)

            # check key action disabled for proxy
            rsp = self.flask_client.get(url, headers=headers)
            self.assertFalse(rsp.json[0]["enabled"])

            user_headers = self.get_headers_for_token(user_id)
            # check key action disabled for proxy
            rsp = self.flask_client.get(url, headers=user_headers)
            self.assertFalse(rsp.json[0]["enabled"])


class ReminderCalendarTestCase(CalendarTestCase):
    SPECIFIC_MONTH_DAYS = [5, 7]

    def setUp(self):
        super().setUp()
        with freeze_time(self.now - relativedelta(days=1)):
            self.uid = self._sign_up_user()
        self.headers = self.get_headers_for_token(self.uid)
        self.base_route = f"/api/extensions/v1beta/user/{self.uid}/reminder"

    def _reminder_base(self):
        hour = self.hour_ahead.hour
        minute = self.hour_ahead.minute
        duration = f"PT{hour}H{minute}M"
        return {
            "durationIso": duration,
            "enabled": True,
            "userId": self.uid,
            "moduleName": "BloodPressure",
            "moduleId": "BloodPressure",
            "moduleConfigId": "5ee836d9ba9fd528807029bc",
        }

    def daily_reminder(self) -> dict:
        reminder = self._reminder_base()
        # every day
        reminder["specificWeekDays"] = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        return reminder

    def weekly_reminder(self) -> dict:
        reminder = self._reminder_base()
        # every Monday and Friday
        reminder["specificWeekDays"] = ["MON", "FRI"]
        return reminder

    def monthly_reminder(self) -> dict:
        reminder = self._reminder_base()
        # every Monday and Friday
        reminder["specificMonthDays"] = self.SPECIFIC_MONTH_DAYS
        return reminder

    @staticmethod
    def prepare_events_for_date(target_dt):
        trigger_dt = target_dt.replace(hour=3)
        if trigger_dt > target_dt:
            trigger_dt -= relativedelta(days=1)
        with freeze_time(trigger_dt):
            prepare_events_for_next_day.apply()

    @patch("sdk.calendar.tasks.execute_events")
    def test_daily_reminder_send_push_notification(self, mock_execute_events):
        tz = pytz.timezone("Europe/Kiev")
        req_obj = UpdateUserProfileRequestObject(id=self.uid, timezone=tz.zone)
        AuthorizationService().update_user_profile(req_obj)
        # set reminder to hour ahead for Kiev time
        now_kiev = (
            self.now.replace(tzinfo=pytz.UTC).astimezone(tz).replace(tzinfo=pytz.UTC)
        )
        hour_ahead_kiev = now_kiev + timedelta(hours=1)
        reminder = self.daily_reminder()
        reminder.update(
            {"durationIso": f"PT{hour_ahead_kiev.hour}H{hour_ahead_kiev.minute}M"}
        )

        with freeze_time(self.now):
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}", json=reminder, headers=self.headers
            )
            self.assertEqual(201, rsp.status_code)

        # checking not sent after 30 minutes
        with freeze_time(self.half_hour_ahead):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_not_called()

        with freeze_time(self.hour_ahead):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            mock_execute_events.delay.reset_mock()

        # checking if actually called daily, calling 5 days in a row
        for days in range(1, 5):
            trigger_time = self.hour_ahead + relativedelta(days=days)
            self.prepare_events_for_date(trigger_time)
            with freeze_time(trigger_time):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_called_once()
                mock_execute_events.delay.reset_mock()

    @patch("sdk.calendar.tasks.execute_events")
    def test_weekly_reminder_send_push_notification(self, mock_execute_events):
        # create weekly reminder for every MON and FRI
        with freeze_time(self.now):
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}", json=self.weekly_reminder(), headers=self.headers
            )
            self.assertEqual(201, rsp.status_code)

        monday = 0
        friday = 4
        nearest_monday = nearest_weekday_date(self.hour_ahead, monday)
        nearest_friday = nearest_weekday_date(self.hour_ahead, friday)
        dates = [nearest_monday, nearest_friday]
        dates.sort()

        for date in dates:
            # running prepare events before expected event to cache next event
            self.prepare_events_for_date(date)
            # checking not sent 30 minutes before expected at nearest weekday
            with freeze_time(date - relativedelta(minutes=30)):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_not_called()

            # checking sent at expected datetime of nearest weekday
            with freeze_time(date):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_called_once()
                mock_execute_events.delay.reset_mock()

            # checking not sent at expected datetime of nearest weekday +1
            next_date = date + relativedelta(days=1)
            self.prepare_events_for_date(next_date)
            with freeze_time(next_date):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_not_called()

    @patch("sdk.calendar.tasks.execute_events")
    def test_monthly_reminder_send_push_notification(self, mock_execute_events):
        with freeze_time(self.now):
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}", json=self.monthly_reminder(), headers=self.headers
            )
            self.assertEqual(201, rsp.status_code)

        # generating nearest month days dates for two month
        dates = list(
            rrule(
                freq=MONTHLY,
                count=len(self.SPECIFIC_MONTH_DAYS) * 2,
                bymonthday=self.SPECIFIC_MONTH_DAYS,
                dtstart=self.hour_ahead,
            )
        )

        for date in dates:
            # running prepare events before expected event to cache next event
            self.prepare_events_for_date(date)
            # checking not sent 30 minutes before expected at nearest day of month
            with freeze_time(date - relativedelta(minutes=30)):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_not_called()

            # checking sent at expected datetime of nearest weekday
            with freeze_time(date):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_called_once()
                mock_execute_events.delay.reset_mock()

            # checking not sent at expected datetime of nearest day of month +1
            next_date = date + relativedelta(days=1)
            self.prepare_events_for_date(next_date)
            with freeze_time(next_date):
                prepare_events_and_execute.apply()
                mock_execute_events.delay.assert_not_called()

    @patch("sdk.calendar.tasks.execute_events")
    def test_reminder_send_push_notification_with_changed_timezone(self, mock_execute):
        # set daily reminder
        with freeze_time(self.now):
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}", json=self.daily_reminder(), headers=self.headers
            )
            self.assertEqual(201, rsp.status_code)

        # generating nearest dates
        dates = list(
            rrule(
                freq=DAILY,
                dtstart=self.hour_ahead,
                until=self.now + relativedelta(days=3),
            )
        )

        # taking first matched date
        date, second_date, _ = dates
        # Checking Kiev TZ to avoid issues with DST
        new_tz = pytz.timezone("Europe/Kiev")
        offset = new_tz.utcoffset(date)
        # checking sent at expected datetime
        with freeze_time(date):
            prepare_events_and_execute.apply()
            mock_execute.delay.assert_called_once()
            mock_execute.delay.reset_mock()

        tz_update_dt = second_date.replace(hour=3)
        if tz_update_dt > second_date:
            tz_update_dt -= relativedelta(days=1)

        with freeze_time(tz_update_dt):
            # changing timezone and checking that not called at same utc time
            auth_service = AuthorizationService()
            auth_service.update_user_profile(
                UpdateUserProfileRequestObject(id=self.uid, timezone=new_tz.zone)
            )

        # checking not sent at UTC expected nearest date
        with freeze_time(second_date):
            prepare_events_and_execute()
            mock_execute.delay.assert_not_called()
            mock_execute.delay.reset_mock()

        # checking if sent at user's tz time by removing difference between UTC and Kiev
        with freeze_time(second_date - offset):
            prepare_events_and_execute()
            mock_execute.delay.assert_called_once()
            mock_execute.delay.reset_mock()

    @patch("sdk.calendar.tasks.execute_events")
    def test_reminder_send_push_notification_after_update(self, mock_execute):
        # set daily reminder
        body = self.daily_reminder()
        with freeze_time(self.now):
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}", json=body, headers=self.headers
            )
            self.assertEqual(201, rsp.status_code)
            reminder_id = rsp.json["id"]

        # generating nearest dates
        rule = rrule(freq=DAILY, count=2, dtstart=self.hour_ahead)
        first_trigger, second_trigger = list(rule)

        # checking sent at expected datetime
        with freeze_time(first_trigger):
            prepare_events_and_execute.apply()
            mock_execute.delay.assert_called_once()
            mock_execute.delay.reset_mock()

        # update reminder just before it should trigger
        with freeze_time(second_trigger - relativedelta(minute=1)):
            hour = (self.hour_ahead + relativedelta(hours=2)).hour
            minute = self.hour_ahead.minute
            body.update({"durationIso": f"PT{hour}H{minute}M"})
            self._refresh_headers()
            rsp = self.flask_client.post(
                f"{self.base_route}/{reminder_id}", json=body, headers=self.headers
            )
            self.assertEqual(200, rsp.status_code)

        # checking not sent at old datetime
        with freeze_time(second_trigger):
            prepare_events_and_execute.apply()
            mock_execute.delay.assert_not_called()
            mock_execute.delay.reset_mock()

        # checking sent at updated datetime
        with freeze_time(second_trigger + relativedelta(hours=2)):
            prepare_events_and_execute.apply()
            mock_execute.delay.assert_called_once()
            mock_execute.delay.reset_mock()

    def test_failure_update_calendar_wrong_event_id(self):
        body = self.daily_reminder()
        rsp = self.flask_client.post(
            f"{self.base_route}/invalid_id", json=body, headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
