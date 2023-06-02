from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta

from extensions.appointment.component import AppointmentComponent
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.router.deployment_requests import (
    UpdateLocalizationsRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.use_case.update_localizations_use_case import (
    UpdateLocalizationsUseCase,
)
from extensions.exceptions import UserErrorCodes
from extensions.key_action.component import KeyActionComponent
from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.use_case.key_action_requests import (
    RetrieveExpiringKeyActionsRequestObject,
)
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from extensions.tests.utils import sample_user
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.router.calendar_request import ExportCalendarRequestObject
from sdk.calendar.utils import get_dt_from_str
from sdk.common.localization.utils import Language
from sdk.common.utils.validators import utc_str_field_to_val
from sdk.versioning.component import VersionComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789c"
PROXY_ID = "5e8f0c74b50aa9656c34744a"
VALID_SUPER_ADMIN_ID = "602d249f78de8b5e09beaeef"
VALID_USER_ID_2 = "5e8f0c74b50aa9656c34789a"
VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
VALID_KEY_ACTION_ID = "5f0f0373d656ed903e5a969e"
TEST_EVENT_ID = "5f0f0373d656ed903e5a969e"


def datetime_to_str(val) -> str:
    return val.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class KeyActionRouterTestCase(ExtensionTestCase):
    SERVER_VERSION = "1.3.1"
    API_VERSION = "v1"
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        AppointmentComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        CalendarComponent(),
        ModuleResultComponent(),
        KeyActionComponent(),
        VersionComponent(server_version=SERVER_VERSION, api_version=API_VERSION),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super().setUp()

        self.now = datetime.utcnow()
        self.headers = self.get_headers_for_token(VALID_USER_ID)
        self.base_url = f"/api/extensions/v1beta/user/{VALID_USER_ID}/key-action"

    def _sign_up_user(self):
        rsp = self.flask_client.post(
            "/api/auth/v1beta/signup", json=sample_user(phone_number="+447475768333")
        )
        return rsp.json["uid"]

    def create_key_action(self, delta_from_trigger="PT0M"):
        service = DeploymentService()
        duration = f"P1WT{self.now.hour}H{self.now.minute}M"
        key_action_cfg = KeyActionConfig.from_dict(
            {
                "title": "hu_ka_groupInfo_title",
                "description": "hu_ka_groupInfo_description",
                "deltaFromTriggerTime": delta_from_trigger,
                "durationFromTrigger": "P1M",
                "type": "MODULE",
                "trigger": "SIGN_UP",
                "durationIso": duration,
                "numberOfNotifications": 0,
                "moduleId": "BloodPressure",
                "moduleConfigId": "5f1824ba504787d8d89ebeaf",
                "instanceExpiresIn": "P1W",
            }
        )
        service.create_key_action(
            deployment_id=VALID_DEPLOYMENT_ID, key_action=key_action_cfg
        )

    def update_localizations(self):
        body = {
            "en": {
                "hu_ka_groupInfo_title": "We need some more information from you",
                "hu_ka_groupInfo_description": "You have a new task for the AZ:CONNECT EU study. Please complete as soon as you can.",
            },
            "de": {
                "hu_ka_groupInfo_title": "Wir benötigen noch einige Informationen über Sie",
                "hu_ka_groupInfo_description": "Sie haben eine neue Aufgabe für die AZ-COnnect-EU-Studie. Bitte erledigen Sie diese so schnell wie möglich.",
            },
        }
        request_object = UpdateLocalizationsRequestObject.from_dict(
            {
                UpdateLocalizationsRequestObject.DEPLOYMENT_ID: VALID_DEPLOYMENT_ID,
                UpdateLocalizationsRequestObject.LOCALIZATIONS: body,
            }
        )

        UpdateLocalizationsUseCase().execute(request_object)

    def test_success_retrieve_key_actions(self):
        rsp = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertGreater(len(rsp.json), 0)
        key_action = next(filter(lambda x: x["id"] == TEST_EVENT_ID, rsp.json))
        self.assertNotIn(KeyAction.EXTRA_FIELDS, key_action)
        # check if timezone was injected correctly
        date = get_dt_from_str(key_action[KeyAction.START_DATE_TIME])
        self.assertEqual(21, date.hour)

    def test_success_retrieve_key_actions_timeframe_simple(self):
        relative_day = self.now.replace(hour=0, minute=0) + relativedelta(days=7)
        query_params = {
            "start": utc_str_field_to_val(relative_day),
            "end": utc_str_field_to_val(relative_day + relativedelta(days=7)),
        }
        rsp = self.flask_client.get(
            self.base_url + "/timeframe",
            headers=self.headers,
            query_string=query_params,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertGreater(len(rsp.json), 0)
        key_action = next(filter(lambda x: x["id"] == TEST_EVENT_ID, rsp.json))
        # check if timezone was injected correctly
        date = get_dt_from_str(key_action[KeyAction.START_DATE_TIME])
        self.assertEqual(21, date.hour)

    def test_success_retrieve_key_actions_timeframe(self):
        self.create_key_action()
        self.update_localizations()
        user_id = self._sign_up_user()

        relative_day = self.now.replace(hour=0, minute=0) + relativedelta(days=7)
        query_params = {
            "start": utc_str_field_to_val(relative_day),
            "end": utc_str_field_to_val(relative_day + relativedelta(days=7)),
        }
        headers = self.get_headers_for_token(user_id)
        url = self.base_url.replace(VALID_USER_ID, user_id) + "/timeframe"

        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(200, rsp.status_code)

        self.assertEqual(2, len(rsp.json))

        self.assertEqual(
            rsp.json[0][KeyAction.TITLE], "We need some more information from you"
        )

        start = utc_str_field_to_val(relative_day - relativedelta(months=1))
        end = utc_str_field_to_val(relative_day - relativedelta(minutes=1))
        query_params = {"start": start, "end": end}

        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(200, rsp.status_code)

        self.assertEqual(1, len(rsp.json))

        start = utc_str_field_to_val(relative_day)
        end = utc_str_field_to_val(relative_day + relativedelta(months=1))
        query_params = {"start": start, "end": end}

        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_key_actions_only_future_events(self):
        self.create_key_action()
        self.create_key_action(delta_from_trigger="P1D")
        user_id = self._sign_up_user()

        relative_day = self.now
        query_params = {
            "start": utc_str_field_to_val(relative_day),
            "end": utc_str_field_to_val(relative_day + relativedelta(days=2)),
            "allowPastEvents": False,
        }
        headers = self.get_headers_for_token(user_id)
        url = self.base_url.replace(VALID_USER_ID, user_id) + "/timeframe"

        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(200, rsp.status_code)

        self.assertEqual(1, len(rsp.json))

    def test_success_retrieve_key_actions_only_expiring_events(self):
        self.create_key_action()
        self.create_key_action(delta_from_trigger="-P6D")
        user_id = self._sign_up_user()
        headers = self.get_headers_for_token(user_id)
        base_url = self.base_url.replace(VALID_USER_ID, user_id)

        expiring_url = base_url + "/expiring"

        rsp = self.flask_client.get(expiring_url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))

        # complete key action
        key_action = rsp.json[0]
        complete_event_url = base_url + f"/{key_action['id']}"
        complete_event_body = {
            KeyAction.START_DATE_TIME: key_action["startDateTime"],
            KeyAction.END_DATE_TIME: key_action["endDateTime"],
            KeyAction.MODEL: KeyAction.__name__,
        }
        rsp = self.flask_client.post(
            complete_event_url, json=complete_event_body, headers=headers
        )
        self.assertEqual(201, rsp.status_code, rsp.json.get("error"))

        rsp = self.flask_client.get(expiring_url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json))

        rsp = self.flask_client.get(
            expiring_url,
            query_string={
                RetrieveExpiringKeyActionsRequestObject.ONLY_ENABLED: "false"
            },
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))

    def test_success_retrieve_key_actions_timeframe_with_valid_language(self):
        self.create_key_action()
        self.update_localizations()
        user_id = self._sign_up_user()

        relative_day = self.now.replace(hour=0, minute=0) + relativedelta(days=7)
        query_params = {
            "start": utc_str_field_to_val(relative_day),
            "end": utc_str_field_to_val(relative_day + relativedelta(days=7)),
        }
        headers = self.get_headers_for_token(user_id)
        url = self.base_url.replace(VALID_USER_ID, user_id) + "/timeframe"

        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(
            rsp.json[0][KeyAction.TITLE], "We need some more information from you"
        )

        headers.update({"x-hu-locale": Language.DE})
        rsp = self.flask_client.get(url, headers=headers, query_string=query_params)
        self.assertEqual(
            rsp.json[0][KeyAction.TITLE],
            "Wir benötigen noch einige Informationen über Sie",
        )

    def test_success_retrieve_key_actions_with_valid_language(self):
        self.create_key_action()
        self.update_localizations()
        user_id = self._sign_up_user()

        headers = self.get_headers_for_token(user_id)

        url = self.base_url.replace(VALID_USER_ID, user_id)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(
            rsp.json[0][KeyAction.TITLE], "We need some more information from you"
        )

        headers.update({"x-hu-locale": Language.DE})
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(
            rsp.json[0]["title"], "Wir benötigen noch einige Informationen über Sie"
        )

    def test_success_create_key_action_log(self):
        rsp = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertGreater(len(rsp.json), 0)
        self.assertTrue(rsp.json[0]["enabled"])

        key_action = rsp.json[0]
        body = {
            "startDateTime": key_action["startDateTime"],
            "endDateTime": key_action["endDateTime"],
            "model": "KeyAction",
        }
        rsp = self.flask_client.post(
            f"{self.base_url}/{VALID_KEY_ACTION_ID}", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

        rsp = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertGreater(len(rsp.json), 0)
        self.assertFalse(rsp.json[0]["enabled"])
        self.assertIn(KeyAction.COMPLETE_DATE_TIME, rsp.json[0])

    def test_success_create_key_action_log_by_proxy(self):
        headers = self.get_headers_for_token(PROXY_ID)
        rsp = self.flask_client.get(self.base_url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertTrue(rsp.json[0]["enabled"])

        key_action = rsp.json[0]
        body = {
            "startDateTime": key_action["startDateTime"],
            "endDateTime": key_action["endDateTime"],
            "model": "KeyAction",
        }
        rsp = self.flask_client.post(
            f"{self.base_url}/{VALID_KEY_ACTION_ID}", json=body, headers=headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_create_log_on_module_result_submit(self):
        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)

        module_result = [
            {
                "type": "Weight",
                "deviceName": "iOS",
                "deploymentId": VALID_DEPLOYMENT_ID,
                "startDateTime": utc_str_field_to_val(datetime.utcnow()),
                "value": 80.0,
            }
        ]
        res = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Weight",
            json=module_result,
            headers=self.headers,
        )
        self.assertEqual(201, res.status_code)

        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)
        disabled = [item for item in res.json if not item["enabled"]]
        self.assertEqual(1, len(disabled))

    def test_create_log_on_questionnaire_submit(self):
        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)

        module_result = [
            {
                "type": "Questionnaire",
                "deviceName": "iOS",
                "deploymentId": VALID_DEPLOYMENT_ID,
                "startDateTime": datetime_to_str(datetime.utcnow()),
                "questionnaireId": "d7c92a9e-ca3b-4f73-824e-3b1ac3b5141d",
                "questionnaireName": "PAM Questionnaire",
                "value": 250.5,
                "answers": [
                    {
                        "answerText": "Answer",
                        "answerScore": 55,
                        "id": "5ee0d29a58e7994d8633037c",
                        "questionId": "5ee0d29a58e7994d8633037c",
                        "question": "Simple Question 1",
                    },
                    {
                        "answerText": "Answer",
                        "answerScore": 55,
                        "id": "5ee0d29a58e7994d8633037c",
                        "questionId": "5ee0d29a58e7994d8633037d",
                        "question": "Simple Question 2",
                    },
                ],
            }
        ]

        res = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Questionnaire",
            json=module_result,
            headers=self.headers,
        )
        self.assertEqual(201, res.status_code)

        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)
        disabled = [item for item in res.json if not item["enabled"]]
        self.assertEqual(1, len(disabled))

    def test_create_log_on_questionnaire_submit_with_module_config_id(self):
        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)

        module_result = [
            {
                "type": "Questionnaire",
                "deviceName": "iOS",
                "deploymentId": VALID_DEPLOYMENT_ID,
                "startDateTime": datetime_to_str(datetime.utcnow()),
                "questionnaireId": "test",
                "questionnaireName": "PAM Questionnaire",
                "value": 250.5,
                "answers": [
                    {
                        "answerText": "Answer",
                        "answerScore": 55,
                        "id": "5ee0d29a58e7994d8633037c",
                        "questionId": "5ee0d29a58e7994d8633037c",
                        "question": "Simple Question 1",
                    },
                    {
                        "answerText": "Answer",
                        "answerScore": 55,
                        "id": "5ee0d29a58e7994d8633037c",
                        "questionId": "5ee0d29a58e7994d8633037d",
                        "question": "Simple Question 2",
                    },
                ],
            }
        ]

        res = self.flask_client.post(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/Questionnaire",
            json=module_result,
            query_string={"moduleConfigId": "5f1824ba504787d8d89ebeb0"},
            headers=self.headers,
        )
        self.assertEqual(201, res.status_code)

        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)
        disabled = [item for item in res.json if not item["enabled"]]
        self.assertEqual(1, len(disabled))

    def test_failure_export_not_valid_user_id(self):
        self.test_server.config.server.debugRouter = True
        rsp = self.flask_client.get(f"/api/calendar/v1beta/user/not_valid_id/export")
        self.assertEqual(403, rsp.status_code)

    def test_failure_export_calendar_with_key_actions(self):
        rsp = self.flask_client.get(f"/api/calendar/v1beta/user/{VALID_USER_ID}/export")
        self.assertEqual(401, rsp.status_code)

    def test_success_export_calendar_with_key_actions_debug_true(self):
        self.test_server.config.server.debugRouter = True
        data = {
            ExportCalendarRequestObject.START: "2020-11-01T00:00:00.000Z",
            ExportCalendarRequestObject.END: "2021-12-01T00:00:00.000Z",
        }
        rsp = self.flask_client.get(
            f"/api/calendar/v1beta/user/{VALID_USER_ID}/export", query_string=data
        )
        self.assertEqual(200, rsp.status_code)
        self.assertTrue("BEGIN:VEVENT" in rsp.data.decode())

    def test_success_delete_user_with_key_actions(self):
        res = self.flask_client.get(self.base_url, headers=self.headers)
        self.assertGreater(len(res.json), 0)

        super_admin_headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        del_user_path = f"/api/extensions/v1beta/user/{VALID_USER_ID}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=super_admin_headers)
        self.assertEqual(rsp.status_code, 204)

        rsp = self.flask_client.get(self.base_url, headers=super_admin_headers)
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp.json["code"])
