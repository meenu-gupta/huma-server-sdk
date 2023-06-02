from datetime import datetime
from pathlib import Path

from bson import ObjectId
from freezegun import freeze_time

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.component import KeyActionComponent
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.repo.mongo_calendar_repository import MongoCalendarRepository
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.validators import utc_str_val_to_field

VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_ID_WITH_SURGERY_RULES = "60cf1b36a57e9f8104655274"
VALID_ADMIN_FROM_DEPLOYMENT_WITH_SURGERY_DATE_RULES = "60cf1beae10b81d781bac6ab"
VALID_ADMIN_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER1_ID = "5e8f0c74b50aa9656c34789a"
VALID_USER2_ID = "5e8f0c74b50aa9656c34789c"
VALID_KEY_ACTION_CONFIG_ID = "5f078582c565202bd6cb03af"

INVALID_DEPLOYMENT_ID = "5d386cc6ff885918d96eda3a"
INVALID_KEY_ACTION_CONFIG_ID = "5d386cc6ff885918d96eda3a"

KEY_ACTION_MODULE_TYPE = KeyActionConfig.Type.MODULE.value
KEY_ACTION_LEARN_TYPE = KeyActionConfig.Type.LEARN.value


def parse_date_string(val) -> datetime:
    if isinstance(val, datetime):
        return val

    try:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")


def simple_key_action_config(type_: str, is_for_next_hour=False):
    _dict = {
        KeyActionConfig.TITLE: "Test Key Action",
        KeyActionConfig.DESCRIPTION: "Test Key Action Description",
        KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "PT0M",
        KeyActionConfig.DURATION_FROM_TRIGGER: "P99Y",
        KeyActionConfig.TYPE: type_,
        KeyActionConfig.TRIGGER: "SIGN_UP",
        KeyActionConfig.DURATION_ISO: "P1DT15H25M",
        KeyActionConfig.NUMBER_OF_NOTIFICATIONS: 3,
        KeyActionConfig.LEARN_ARTICLE_ID: "5e8c58176207e5f78023e655",
        KeyActionConfig.MODULE_ID: "BloodPressure",
        KeyActionConfig.MODULE_CONFIG_ID: "5e94b2007773091c9a592650",
    }
    if type_ == KEY_ACTION_MODULE_TYPE:
        _dict.pop(KeyActionConfig.LEARN_ARTICLE_ID, None)
    elif type_ == KEY_ACTION_LEARN_TYPE:
        _dict.pop(KeyActionConfig.MODULE_ID, None)
        _dict.pop(KeyActionConfig.MODULE_CONFIG_ID, None)

    if is_for_next_hour:
        now = datetime.utcnow()
        hour = now.hour + 1
        if hour == 24:
            hour = 0
        minute = now.minute
        _dict.update({KeyActionConfig.DURATION_ISO: f"P1DT{hour}H{minute}M"})

    return _dict


def created_key_action_config():
    return {
        KeyActionConfig.DESCRIPTION: "Some stuff",
        KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "PT0M",
        KeyActionConfig.DURATION_FROM_TRIGGER: "P6M",
        KeyActionConfig.TYPE: KEY_ACTION_MODULE_TYPE,
        KeyActionConfig.TRIGGER: "SIGN_UP",
        KeyActionConfig.DURATION_ISO: "P1DT9H2M",
        KeyActionConfig.NUMBER_OF_NOTIFICATIONS: 3,
        KeyActionConfig.MODULE_ID: "BloodPressure",
        KeyActionConfig.MODULE_CONFIG_ID: "5e94b2007773091c9a592650",
    }


def existing_key_action():
    return {
        KeyActionConfig.TITLE: "PAM Questionnaire",
        KeyActionConfig.DESCRIPTION: "You have a new activity for the DeTAP study. Please complete as soon as you are able to.",
        KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "PT0M",
        KeyActionConfig.DURATION_FROM_TRIGGER: "P6M",
        KeyActionConfig.TYPE: KEY_ACTION_MODULE_TYPE,
        KeyActionConfig.TRIGGER: "SIGN_UP",
        KeyActionConfig.DURATION_ISO: "P1DT9H2M",
        KeyActionConfig.NUMBER_OF_NOTIFICATIONS: 3,
        KeyActionConfig.MODULE_ID: "BloodPressure",
        KeyActionConfig.MODULE_CONFIG_ID: "5e94b2007773091c9a592650",
    }


class KeyActionConfigTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        CalendarComponent(),
        DeploymentComponent(),
        KeyActionComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/key_actions_dump.json")]
    override_config = {"server.deployment.userProfileValidation": "true"}

    @classmethod
    def setUpClass(cls) -> None:
        super(KeyActionConfigTestCase, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(VALID_ADMIN_ID)
        cls.base_url = "/api/extensions/v1beta/deployment"
        cls.user_id = "28d381b2d6b432c95036fc06"

    def url(self, url: str):
        return f"{self.base_url}{url}"

    def post(self, body, url=None):
        return self.flask_client.post(
            url or self.url(f"/{VALID_DEPLOYMENT_ID}/key-action"),
            json=body,
            headers=self.headers,
        )

    def put(self, body, url=None):
        return self.flask_client.put(
            url
            or self.url(
                f"/{VALID_DEPLOYMENT_ID}/key-action/{VALID_KEY_ACTION_CONFIG_ID}"
            ),
            json=body,
            headers=self.headers,
        )

    def _get_user_events(self, user_id: str) -> list:
        return list(self.mongo_database["calendar"].find({"userId": ObjectId(user_id)}))

    def _get_user_events_count(self, user_id: str) -> list:
        return self.mongo_database["calendar"].count_documents(
            {"userId": ObjectId(user_id)}
        )

    def _cached_event_count(self, user_id: str):
        name = MongoCalendarRepository.CACHE_CALENDAR_COLLECTION
        collection = self.mongo_database[name]
        return collection.count_documents({"userId": ObjectId(user_id)})

    def test_success_create_key_action_on_sign_up(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup",
            json={
                "method": 0,
                "email": "test@gmail.com",
                "displayName": "test",
                "validationData": {"activationCode": "53924415"},
                "userAttributes": {
                    "familyName": "test",
                    "givenName": "test",
                    "dob": "1988-02-20",
                    "gender": "MALE",
                },
                "clientId": "ctest1",
                "projectId": "ptest1",
            },
        )
        self.assertEqual(200, rsp.status_code)
        result = self.mongo_database["calendar"].find_one(
            {"userId": ObjectId(rsp.json["uid"])}
        )
        self.assertIsNotNone(result)

    @freeze_time("2012-12-24")
    def _update_user_surgery_date(self, user_id, surgery_date):
        user_id = user_id
        surgery_str_time = surgery_date
        body = {
            "id": user_id,
            "status": 1,
            "displayName": "admin",
            "familyName": "hey",
            "dob": "1988-02-20",
            "gender": "MALE",
            "givenName": "New test name",
            User.SURGERY_DATE_TIME: surgery_str_time,
        }
        headers = self.get_headers_for_token(VALID_ADMIN_ID)
        return self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}", json=body, headers=headers
        )

    def test_success_create_surgery_key_action_on_user_update(self):
        surgery_str_time = "2012-12-25T00:00:00Z"
        surgery_datetime_object = utc_str_val_to_field(surgery_str_time)
        rsp = self._update_user_surgery_date(self.user_id, surgery_str_time)
        self.assertEqual(200, rsp.status_code)
        result = list(
            self.mongo_database["calendar"].find({"userId": ObjectId(self.user_id)})
        )
        self.assertIsNotNone(result)

        for i in result:
            if i["title"] == "SURGERY negative deltaFromTriggerTime":
                self.assertLess(i["startDateTime"], surgery_datetime_object)
            elif i["title"] == "SURGERY positive deltaFromTriggerTime":
                self.assertGreater(i["endDateTime"], surgery_datetime_object)

    @freeze_time("2012-12-24")
    def test_success_set_surgery_date_deployment_has_surgery_date_rules(self):
        body = {User.SURGERY_DATE_TIME: "2012-12-25"}
        user_id = VALID_ADMIN_FROM_DEPLOYMENT_WITH_SURGERY_DATE_RULES
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}",
            json=body,
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(200, rsp.status_code)

    @freeze_time("2012-12-24")
    def test_failure_set_surgery_date_deployment_has_surgery_date_rules_less_past_limit(
        self,
    ):
        body = {User.SURGERY_DATE_TIME: "2011-12-25"}
        user_id = VALID_ADMIN_FROM_DEPLOYMENT_WITH_SURGERY_DATE_RULES
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}",
            json=body,
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["message"], "Surgery date should be after 2012-12-17")

    @freeze_time("2012-12-24")
    def test_failure_set_surgery_date_deployment_has_surgery_date_rules_greater_max_limit(
        self,
    ):
        body = {User.SURGERY_DATE_TIME: "2013-12-25"}
        user_id = VALID_ADMIN_FROM_DEPLOYMENT_WITH_SURGERY_DATE_RULES
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{user_id}",
            json=body,
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(
            rsp.json["message"], "Surgery date should be before 2012-12-31"
        )

    def test_delete_past_events_when_surgery_date_changed(self):
        surgery_str_time = "2012-12-25T00:00:00Z"
        rsp = self._update_user_surgery_date(self.user_id, surgery_str_time)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self._get_user_events_count(self.user_id), 2)

        # changing date once again
        surgery_str_time = "2012-12-26T00:00:00Z"
        rsp = self._update_user_surgery_date(self.user_id, surgery_str_time)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self._get_user_events_count(self.user_id), 2)

    def test_success_set_current_date_as_surgery_date(self):
        surgery_str_time = datetime.now().replace(hour=0, minute=0, second=0)
        body = {User.SURGERY_DATE_TIME: surgery_str_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    @freeze_time("2020-12-24")
    def test_failure_create_surgery_key_action_past_date(self):
        surgery_str_time = "2012-12-02T00:00:00Z"
        body = {User.SURGERY_DATE_TIME: surgery_str_time}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}",
            json=body,
            headers=self.get_headers_for_token(VALID_ADMIN_ID),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(0, self._get_user_events_count(self.user_id))

    def test_events_updated_only_for_one_user(self):
        # creating events for 1 user
        surgery_str_time = "2012-12-25T00:00:00Z"
        rsp = self._update_user_surgery_date(self.user_id, surgery_str_time)
        self.assertEqual(200, rsp.status_code)
        events_first_user = self._get_user_events(self.user_id)
        self.assertEqual(2, len(events_first_user))

        # creating events for 2nd user
        sec_user_id = "28d381b2d6b432c95036fc03"
        surgery_str_time = "2012-12-26T00:00:00Z"
        rsp = self._update_user_surgery_date(sec_user_id, surgery_str_time)
        self.assertEqual(200, rsp.status_code)
        events_sec_user = self._get_user_events(sec_user_id)
        self.assertEqual(2, len(events_sec_user))

        # verifying that update of 2nd user, hasn't changed calendar for the first user
        events_first_user_after_update = self._get_user_events(self.user_id)
        self.assertEqual(events_first_user, events_first_user_after_update)
        self.assertNotEqual(events_sec_user, events_first_user)

    def test_failure_create_surgery_key_action_surgery_date_none(self):
        rsp = self._update_user_surgery_date(user_id=self.user_id, surgery_date=None)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, self._get_user_events_count(self.user_id))

    def test_not_creating_surgery_key_action_when_no_surgeryDateTime_passed(self):
        # not creating key actions when surgeryDateTime was not changed
        # during the user profile update

        body = {
            "id": self.user_id,
            "status": 1,
            "displayName": "admin",
            "familyName": "hey",
            "dob": "1988-02-20",
            "gender": "MALE",
            "givenName": "New test name",
        }
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, self._get_user_events_count(self.user_id))

    def test_success_update_key_action_on_key_action_config_update(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        now = datetime.utcnow()
        hour = now.hour + 1
        if hour == 24:
            hour = 0
        minute = now.minute
        body.update({"durationIso": f"P1DT{hour}H{minute}M"})
        rsp = self.put(body)
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        for event in rsp.json:
            date = parse_date_string(event["startDateTime"])
            self.assertEqual(hour, date.hour)
            self.assertEqual(minute, date.minute)

        next_day_event_count = self._cached_event_count(VALID_USER1_ID)
        self.assertEqual(3, next_day_event_count)

    def test_create_key_action_after_key_action_config_created(self):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        user1_events_len = len(rsp.json)

        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER2_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER2_ID),
        )
        user2_events_len = len(rsp.json)

        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE, is_for_next_hour=True)
        rsp = self.post(body)
        self.assertEqual(201, rsp.status_code)

        # check if user of same deployment has key actions
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        self.assertGreater(len(rsp.json), user1_events_len)

        # check if user of another deployment doesn't have key actions
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER2_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER2_ID),
        )
        self.assertEqual(len(rsp.json), user2_events_len)

        next_day_event_count = self._cached_event_count(VALID_USER1_ID)
        self.assertEqual(1, next_day_event_count)

    def test_delete_key_action_after_key_action_config_deleted(self):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        self.assertEqual(200, rsp.status_code)
        event_len = len(rsp.json)
        rsp = self.flask_client.delete(
            self.url(f"/{VALID_DEPLOYMENT_ID}/key-action/{VALID_KEY_ACTION_CONFIG_ID}"),
            headers=self.headers,
        )
        self.assertEqual(204, rsp.status_code)
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        self.assertGreater(event_len, len(rsp.json))

    def test_success_skip_update_key_action_on_key_action_config_update(self):
        body = existing_key_action()
        rsp = self.put(body)
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER1_ID}/key-action",
            headers=self.get_headers_for_token(VALID_USER1_ID),
        )
        for event in rsp.json:
            date = parse_date_string(event["startDateTime"])
            self.assertEqual(9, date.hour)
            self.assertEqual(2, date.minute)

    def test_success_create_key_action_learn(self):
        body = simple_key_action_config(KeyActionConfig.Type.LEARN.value)
        rsp = self.post(body)
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[KeyAction.ID])

    def test_success_update_key_action_remove_notify_every(self):
        body = simple_key_action_config(KeyActionConfig.Type.LEARN.value)
        body[KeyActionConfig.NOTIFY_EVERY] = "P1WT"
        rsp = self.post(body)
        self.assertEqual(201, rsp.status_code)
        key_action_id = rsp.json[KeyAction.ID]
        self.assertIsNotNone(key_action_id)

        body.pop(KeyActionConfig.NOTIFY_EVERY, None)
        self.put(body, self.url(f"/{VALID_DEPLOYMENT_ID}/key-action/{key_action_id}"))
        result = self.mongo_database["deployment"].find_one(
            {"_id": ObjectId(VALID_DEPLOYMENT_ID)}
        )
        updated_key_action = next(
            filter(
                lambda x: x[KeyActionConfig.ID] == ObjectId(key_action_id),
                [item for item in result[Deployment.KEY_ACTIONS]],
            )
        )
        self.assertNotIn(KeyActionConfig.NOTIFY_EVERY, updated_key_action.keys())

    def test_success_create_key_action_module(self):
        body = simple_key_action_config(KeyActionConfig.Type.MODULE.value)
        rsp = self.post(body)
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[KeyAction.ID])

    def test_failure_create_key_action_module_invalid_duration_iso(self):
        body = simple_key_action_config(KeyActionConfig.Type.MODULE.value)
        req_body = {**body, KeyActionConfig.DURATION_ISO: "P0DT0M0S"}
        rsp = self.post(req_body)
        self.assertEqual(403, rsp.status_code)

        req_body = {**body, KeyActionConfig.NOTIFY_EVERY: "P0DT0M0S"}
        rsp = self.post(req_body)
        self.assertEqual(403, rsp.status_code)

    def _get_deployment_response(self):
        rsp = self.flask_client.get(
            self.url(f"/{VALID_DEPLOYMENT_ID}"),
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def test_success_deployment_update_dt_gets_updated(self):
        deployment = self._get_deployment_response()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        body = simple_key_action_config(KeyActionConfig.Type.MODULE.value)
        rsp = self.post(body)
        self.assertEqual(201, rsp.status_code)
        created_id = rsp.json[KeyAction.ID]

        deployment = self._get_deployment_response()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])
        update_date_after_creation = deployment[Deployment.UPDATE_DATE_TIME]

        # updating newly created key action
        body = simple_key_action_config(KeyActionConfig.Type.MODULE.value)
        body.update({"title": "New title for test config"})
        rsp = self.put({**body, KeyAction.ID: created_id})
        self.assertEqual(200, rsp.status_code)

        deployment = self._get_deployment_response()
        self.assertLess(
            update_date_after_creation,
            deployment[Deployment.UPDATE_DATE_TIME],
        )

    def test_failure_create_key_action_wrong_type(self):
        body = simple_key_action_config("TEST")
        rsp = self.post(body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_key_action_odd_key(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        body.update({"learnArticleId": "5d386cc6ff885918d96eda3a"})
        rsp = self.post(body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_key_action_wrong_deployment_id(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        rsp = self.post(body, self.url(f"/{INVALID_DEPLOYMENT_ID}/key-action"))
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_create_key_action_with_id(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        body.update({"id": "5d386cc6ff885918d96eda3a"})
        rsp = self.post(body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_key_action_module_no_module_id(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        body.pop("moduleId", None)
        rsp = self.post(body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_key_action_module_no_module_config_id(self):
        body = simple_key_action_config(KEY_ACTION_MODULE_TYPE)
        body.pop("moduleConfigId", None)
        rsp = self.post(body)
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_success_retrieve_key_actions(self):
        rsp = self.flask_client.get(
            self.url(f"/{VALID_DEPLOYMENT_ID}"), headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json["keyActions"]))
        key_action = rsp.json["keyActions"][0]
        self.assertNotIn(KeyAction.EXTRA_FIELDS, key_action)
        self.assertIn(KeyAction.MODULE_ID, key_action)
        self.assertIn(KeyAction.MODULE_CONFIG_ID, key_action)

    def test_success_update_key_action(self):
        body = created_key_action_config()
        body.update({"title": "New title for test config"})
        rsp = self.put(body)
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            self.url(f"/{VALID_DEPLOYMENT_ID}"), headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        deployment = rsp.json
        self.assertEqual(1, len(deployment["keyActions"]))
        self.assertEqual(body["title"], deployment["keyActions"][0]["title"])

    def test_failure_update_key_action_wrong_id(self):
        body = created_key_action_config()
        body.update({"title": "New title for test config"})
        rsp = self.put(
            body,
            url=self.url(
                f"/{VALID_DEPLOYMENT_ID}/key-action/{INVALID_KEY_ACTION_CONFIG_ID}"
            ),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_update_key_action_wrong_deployment_id(self):
        body = created_key_action_config()
        body.update({"title": "New title for test config"})
        rsp = self.put(
            body,
            url=self.url(
                f"/{INVALID_DEPLOYMENT_ID}/key-action/{VALID_KEY_ACTION_CONFIG_ID}"
            ),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_update_key_action_wrong_iso(self):

        body = created_key_action_config()
        req_body = {**body, KeyActionConfig.DURATION_ISO: "P0DT0M0S"}
        rsp = self.put(req_body)
        self.assertEqual(403, rsp.status_code)

        body = created_key_action_config()
        req_body = {**body, KeyActionConfig.NOTIFY_EVERY: "P0D"}
        rsp = self.put(req_body)
        self.assertEqual(403, rsp.status_code)

    def test_success_delete_key_action(self):
        rsp = self.flask_client.delete(
            self.url(f"/{VALID_DEPLOYMENT_ID}/key-action/{VALID_KEY_ACTION_CONFIG_ID}"),
            headers=self.headers,
        )
        self.assertEqual(204, rsp.status_code)

    def test_failure_delete_key_action_wrong_id(self):
        rsp = self.flask_client.delete(
            self.url(
                f"/{VALID_DEPLOYMENT_ID}/key-action/{INVALID_KEY_ACTION_CONFIG_ID}"
            ),
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_delete_key_action_wrong_deployment_id(self):
        rsp = self.flask_client.delete(
            self.url(
                f"/{VALID_DEPLOYMENT_ID}/key-action/{INVALID_KEY_ACTION_CONFIG_ID}"
            ),
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])
