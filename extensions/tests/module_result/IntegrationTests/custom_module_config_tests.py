from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import Deployment
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.module_config import ModuleConfig
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from extensions.tests.module_result.IntegrationTests.test_samples import (
    VALID_DEPLOYMENT_ID,
)
from extensions.tests.module_result.UnitTests.test_helpers import (
    custom_config_req_body,
    ACCESS_CONTROLLER_ID,
    ADMIN_ID,
    MODULE_CONFIG_ID,
    PATIENT_ID,
    PROXY_ID,
)


class CustomModuleConfigRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    override_config = {"server.moduleResult.enableAuthz": "true"}

    def setUp(self):
        super().setUp()

        self.custom_mc_route = (
            f"/api/extensions/v1beta/user/{PATIENT_ID}/moduleConfig/{MODULE_CONFIG_ID}"
        )
        self.custom_module_configs = (
            f"/api/extensions/v1beta/user/{PATIENT_ID}/moduleConfigs"
        )
        self.custom_mc_log_route = f"/api/extensions/v1beta/user/{PATIENT_ID}/moduleConfig/{MODULE_CONFIG_ID}/logs"

    def test_success_create_custom_config(self):
        body = custom_config_req_body("create")
        rsp = self.flask_client.put(
            self.custom_mc_route,
            json=body,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], MODULE_CONFIG_ID)

        self._test_custom_config_logs(2, 2, self.custom_mc_log_route)

    def test_failure_create_custom_config_flag_disabled(self):
        self._disable_custom_config_flag()
        body = custom_config_req_body("create")
        rsp = self.flask_client.put(
            self.custom_mc_route,
            json=body,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_create_custom_config_unauthorized(self):
        body = custom_config_req_body("create")
        not_authorized_role_ids = [ACCESS_CONTROLLER_ID, PROXY_ID]
        for role_id in not_authorized_role_ids:
            rsp = self.flask_client.put(
                self.custom_mc_route,
                json=body,
                headers=self.get_headers_for_token(role_id),
            )
            self.assertEqual(403, rsp.status_code)

    def test_update_custom_config(self):
        body = custom_config_req_body("create")
        self.flask_client.put(
            self.custom_mc_route,
            json=body,
            headers=self.get_headers_for_token(ADMIN_ID),
        )

        body = custom_config_req_body("update")
        rsp = self.flask_client.put(
            self.custom_mc_route,
            json=body,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], MODULE_CONFIG_ID)

        self._test_custom_config_logs(3, 3, self.custom_mc_log_route)
        self._test_custom_config_logs(1, 3, f"{self.custom_mc_log_route}?limit=1")
        self._test_custom_config_logs(1, 3, f"{self.custom_mc_log_route}?skip=2")
        self._test_custom_config_logs(1, 1, f"{self.custom_mc_log_route}?type=SCHEDULE")
        self._test_custom_config_logs(2, 2, f"{self.custom_mc_log_route}?type=RAG")

    def test_retrieve_custom_configs(self):
        body = custom_config_req_body("create")
        self.flask_client.put(
            self.custom_mc_route,
            json=body,
            headers=self.get_headers_for_token(ADMIN_ID),
        )

        rsp = self.flask_client.get(
            self.custom_module_configs,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json["configs"]), 1)

    def test_failure_retrieve_custom_configs_flag_disabled(self):
        self._disable_custom_config_flag()
        rsp = self.flask_client.get(
            self.custom_module_configs,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(404, rsp.status_code)

    def _disable_custom_config_flag(self):
        self.mongo_database.deployment.update_one(
            {Deployment.ID_: ObjectId(VALID_DEPLOYMENT_ID)},
            {"$set": {"features.personalizedConfig": False}},
        )

    def test_failure_retrieve_custom_config_logs_flag_disabled(self):
        self._disable_custom_config_flag()
        rsp = self.flask_client.get(
            self.custom_mc_log_route,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(404, rsp.status_code)

    def _test_custom_config_logs(self, count: int, total: int, route: str):
        rsp = self.flask_client.get(
            route,
            headers=self.get_headers_for_token(ADMIN_ID),
        )
        self.assertEqual(200, rsp.status_code)
        logs = rsp.json.get("logs", [])
        self.assertEqual(len(logs), count)
        self.assertEqual(rsp.json.get("total"), total)
        for log in logs:
            both_exists = (
                ModuleConfig.RAG_THRESHOLDS in log and ModuleConfig.SCHEDULE in log
            )
            none_exists = (
                ModuleConfig.RAG_THRESHOLDS not in log
                and ModuleConfig.SCHEDULE not in log
            )
            if both_exists or none_exists:
                self.fail()
