from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import AZGroupKeyActionTrigger
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import now_str
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_background_information,
    sample_group_information,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.utils.validators import utc_date_to_str
from sdk.versioning.component import VersionComponent

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
CALL_CENTER_STAFF_ID = "601919b5c03550c421c075eb"
SAME_DEPLOYMENT_USER_ID = "5ed803dd5f2f99da73684412"
OTHER_DEPLOYMENT_USER_ID = "5e8f0c74b50aa9656c34789b"
WEIGHT_MODULE_ID = "5f1824ba504787d8d89ebeca"
VALID_KEY_ACTION_ID = "5f07a582c565202bd6cb03af"


class CallCenterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        KeyActionComponent(),
        CalendarComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/roles_dump.json")]
    user_route_template = "api/extensions/v1beta/user/%s"
    override_config = {"server.moduleResult.enableAuthz": "true"}
    key_action_url = f"/api/extensions/v1beta/user/{SAME_DEPLOYMENT_USER_ID}/key-action"

    @classmethod
    def setUpClass(cls) -> None:
        super(CallCenterTestCase, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(CALL_CENTER_STAFF_ID)

    def get_profile(self, user_id: str):
        url = self.user_route_template % user_id
        return self.flask_client.get(url, headers=self.headers)

    def post(self, url, body):
        return self.flask_client.post(url, json=body, headers=self.headers)

    @staticmethod
    def sample_weight(value=100):
        return {
            "deploymentId": DEPLOYMENT_ID,
            "version": 0,
            "deviceName": "iOS",
            "isAggregated": False,
            "startDateTime": now_str(),
            "type": "Weight",
            "value": value,
        }

    def test_success_update_user_profile(self):
        url = self.user_route_template % SAME_DEPLOYMENT_USER_ID
        body = {"timezone": "Europe/Kiev"}
        rsp = self.post(url, body)
        self.assertEqual(200, rsp.status_code)

        rsp = self.get_profile(SAME_DEPLOYMENT_USER_ID)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body["timezone"], rsp.json["timezone"])

    def test_failure_update_user_profile_other_deployment(self):
        url = self.user_route_template % OTHER_DEPLOYMENT_USER_ID
        body = {"timezone": "Europe/Kiev"}
        rsp = self.post(url, body)
        self.assertEqual(403, rsp.status_code)

    def test_success_submit_module_result(self):
        user_url = self.user_route_template % SAME_DEPLOYMENT_USER_ID
        url = f"{user_url}/module-result/Weight"
        body = self.sample_weight()
        rsp = self.post(url, [body])
        self.assertEqual(201, rsp.status_code)

        rsp = self.get_profile(SAME_DEPLOYMENT_USER_ID)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            body["value"],
            rsp.json["recentModuleResults"][WEIGHT_MODULE_ID][0]["Weight"]["value"],
        )

    def test_success_create_log_on_module_result_submit(self):
        user_url = self.user_route_template % SAME_DEPLOYMENT_USER_ID
        url = f"{user_url}/module-result/AZGroupKeyActionTrigger"
        body = sample_group_information()
        vaccine_date = utc_date_to_str(datetime.utcnow() - relativedelta(days=1))
        body.update({AZGroupKeyActionTrigger.FIRST_VACCINE_DATE: vaccine_date})
        rsp = self.post(url, [body])
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(f"{user_url}/key-action", headers=self.headers)
        self.assertGreater(len(rsp.json), 0)
        self.assertTrue(rsp.json[0]["enabled"])

        body = sample_background_information()
        url = f"{user_url}/module-result/BackgroundInformation"
        self.post(url, [body])

        key_action = rsp.json[0]
        body = {
            "startDateTime": key_action["startDateTime"],
            "endDateTime": key_action["endDateTime"],
            "model": "KeyAction",
        }
        rsp = self.flask_client.post(
            f"{self.key_action_url}/{key_action[KeyAction.ID]}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

    def test_failure_submit_module_result_other_deployment(self):
        user_url = self.user_route_template % OTHER_DEPLOYMENT_USER_ID
        url = f"{user_url}/module-result/Weight"
        body = self.sample_weight()
        rsp = self.post(url, [body])
        self.assertEqual(403, rsp.status_code)
