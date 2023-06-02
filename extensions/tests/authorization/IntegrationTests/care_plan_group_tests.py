from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import Deployment
from extensions.key_action.component import KeyActionComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_sign_up_data,
)
from extensions.tests.test_case import ExtensionTestCase
from extensions.twilio_video.component import TwilioVideoComponent
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.notification.component import NotificationComponent

CONFIG_PATH = Path(__file__).with_name("config.test.yaml")

DEPLOYMENT_X_USER_CODE = "53924415"
DEPLOYMENT_X_MANAGER_CODE = "17781957"

DEPLOYMENT_X_EXTENSION_ACTIVATION_CODE_1 = "01"
DEPLOYMENT_X_EXTENSION_ACTIVATION_CODE_2 = "02"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34788d"
VALID_CALL_CENTER_ID = "602fa576c06fe59e3556142a"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT = "600720843111683010a73b4e"
VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT = "6009d2409b0e1f2eab20bbb3"

MILD_GROUP = "com.huma.covid19.mild"
SEVERE_GROUP = "com.huma.covid19.severe"
OBSERVATION_NOTE_ID = "5f15aaea6530a4c3c6db4506"
WEIGHT_ID = "5f1824ba504787d8d89ebeca"
HEIGHT_ID = "5f1824ba504787d8d89ebecb"
JOURNAL_ID = "5f1824ba504787d8d89ebe4a"
NOTIFICATION_PATH = (
    "sdk.common.push_notifications.push_notifications_utils.NotificationService"
)


class MockAuthService:
    g = MagicMock()
    g.user.id = "5e8f0c74b50aa9656c34789b"
    g.user.get_full_name.return_value = "SubmitterName"


class CarePlanGroupTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        CalendarComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        TwilioVideoComponent(),
        NotificationComponent(),
        KeyActionComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
    ]

    auth_route = "/api/auth/v1beta"
    base_path = "/api/extensions/v1beta/user"
    deployment_id = "5d386cc6ff885918d96edb2c"
    manager_id = "5e8f0c74b50aa9656c34789b"
    user_id = "5e8f0c74b50aa9656c34789b"
    user_with_invalid_module_config_id = "5e8f0c74b50aa9656c34789c"
    user_with_invalid_care_plan_group_id = "5e8f0c74b50aa9656c34789e"

    def setUp(self) -> None:
        super().setUp()
        self.base_path = "/api/extensions/v1beta/user"
        self.auth_route = "/api/auth/v1beta"

        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.user_id = "5e8f0c74b50aa9656c34789b"
        self.manager_id = "5e8f0c74b50aa9656c34788d"
        self.user_with_invalid_module_config_id = "5e8f0c74b50aa9656c34789c"
        self.user_with_invalid_care_plan_group_id = "5e8f0c74b50aa9656c34789e"

        self.headers_for_user = self.get_headers_for_token(self.user_id)
        self.headers_for_manager = self.get_headers_for_token(self.manager_id)

        self.calendar_collection = self.mongo_database["calendar"]

    @staticmethod
    def find_item_by_id(item_id, iterable) -> Optional[str]:
        return next(filter(lambda x: x["id"] == item_id, iterable), None)

    def register_user(self, user_data: dict):
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        return user_id

    def events_count(self, user_id: str):
        return self.calendar_collection.count_documents({"userId": ObjectId(user_id)})

    def test_user_create_and_test_default_care_plan_group(self):
        test_id = "5f15aaea6530a4c3c6db4506"
        user = get_sign_up_data("user1@example.com", "user1", DEPLOYMENT_X_USER_CODE)
        user_id = self.register_user(user)

        # check if default care plan group is assigned to the user and check resolved patch
        headers = self.get_headers_for_token(user_id)
        rsp = self.flask_client.get(
            f"{self.base_path}/{user_id}/configuration", headers=headers
        )
        self.assertEqual(rsp.status_code, 200)
        module_configs = rsp.json.get(Deployment.MODULE_CONFIGS)
        self.assertIsNotNone(module_configs)
        self.assertIsNone(self.find_item_by_id(test_id, module_configs))

    def test_assigned_care_plan_group_for_new_user(self):
        code = DEPLOYMENT_X_USER_CODE + DEPLOYMENT_X_EXTENSION_ACTIVATION_CODE_2
        user = get_sign_up_data("user2@example.com", "user2", code)
        user_id = self.register_user(user)

        # check if default care plan group is assigned to the user and check resolved patch
        headers = self.get_headers_for_token(user_id)
        rsp = self.flask_client.get(
            f"{self.base_path}/{user_id}/configuration", headers=headers
        )
        self.assertEqual(rsp.status_code, 200)
        module_configs = rsp.json.get(Deployment.MODULE_CONFIGS)
        self.assertIsNotNone(module_configs)

        # Check Weight module is patched and has a new timesPerDuration
        weight = self.find_item_by_id(WEIGHT_ID, module_configs)
        self.assertIn("schedule", weight)
        self.assertIn("isoDuration", weight["schedule"])
        self.assertEqual(3, weight["schedule"]["timesPerDuration"])

        # Check Journal module is patched to "DISABLED" and not present in configs
        self.assertIsNone(self.find_item_by_id(JOURNAL_ID, module_configs))

        # Check Height module is patched and has a new value for timesOfDay field
        height = self.find_item_by_id(HEIGHT_ID, module_configs)
        self.assertIn("schedule", height)
        self.assertIn("timesOfDay", height["schedule"])

        time_of_day = height["schedule"]["timesOfDay"]
        value = next(filter(lambda x: x == "UPON_WAKING", time_of_day), None)
        self.assertIsNotNone(value)

    def test_failure_create_user_with_invalid_extension_activation_code(self):
        code = DEPLOYMENT_X_USER_CODE + "001"
        user = get_sign_up_data("user1@example.com", "user1", code)
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user)
        self.assertEqual(400, rsp.status_code)

    def test_retrieve_care_plan_groups_for_manager(self):
        headers = self.get_headers_for_token(self.manager_id)
        rsp = self.flask_client.get(
            f"{self.base_path}/{self.manager_id}/deployment/{self.deployment_id}/care-plan-groups",
            headers=headers,
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertIn("groups", rsp.json)
        groups = rsp.json["groups"]
        self.assertIn(MILD_GROUP, groups)
        self.assertIn(Deployment.MODULE_CONFIGS, groups[MILD_GROUP])
        self.assertEqual(10, len(groups[MILD_GROUP][Deployment.MODULE_CONFIGS]))

        self.assertIn(SEVERE_GROUP, groups)
        self.assertIn(Deployment.MODULE_CONFIGS, groups[SEVERE_GROUP])
        self.assertEqual(11, len(groups[SEVERE_GROUP][Deployment.MODULE_CONFIGS]))

        # weight module with replace P1D with P4D
        module_configs = groups[SEVERE_GROUP][Deployment.MODULE_CONFIGS]
        weight_module_config = self.find_item_by_id(WEIGHT_ID, module_configs)
        self.assertIn("schedule", weight_module_config)
        self.assertIn("isoDuration", weight_module_config["schedule"])

        # this also checks if string "3" is converted to int successfully
        self.assertEqual(3, weight_module_config["schedule"]["timesPerDuration"])

    def test_success_retrieve_care_plan_groups_by_call_center(self):
        headers = self.get_headers_for_token(VALID_CALL_CENTER_ID)
        url = f"{self.base_path}/%s/deployment/%s/care-plan-groups"
        rsp = self.flask_client.get(
            url % (VALID_CALL_CENTER_ID, self.deployment_id),
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_care_plan_group_log_by_custom_role_id(self):
        headers = self.get_headers_for_token(
            VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
        )
        url = f"{self.base_path}/%s/deployment/%s/care-plan-group-log"
        rsp = self.flask_client.get(
            url % (VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT, self.deployment_id),
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)

    @patch(NOTIFICATION_PATH)
    def test_success_update_user_care_plan_group(self, mock_service):
        new_care_plan_group_id = SEVERE_GROUP
        data = {"carePlanGroupId": new_care_plan_group_id, "note": ""}
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.user_id}/deployment/{self.deployment_id}/care-plan-group",
            headers=self.headers_for_manager,
            json=data,
        )
        self.assertEqual(rsp.status_code, 200)
        user_id = rsp.json["id"]
        self.assertIsNotNone(user_id)
        mock_service.push_for_user.asser_called_once()

        rsp = self.flask_client.get(
            f"{self.base_path}/{self.user_id}",
            headers=self.headers_for_user,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(new_care_plan_group_id, rsp.json["carePlanGroupId"])

    @patch(NOTIFICATION_PATH)
    def test_success_update_user_care_plan_group_by_contributor(self, mock_noti):
        headers = self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X)
        new_care_plan_group_id = "com.huma.covid19.severe"
        data = {"carePlanGroupId": new_care_plan_group_id, "note": ""}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/deployment/{self.deployment_id}/care-plan-group",
            headers=headers,
            json=data,
        )
        self.assertEqual(rsp.status_code, 200)
        user_id = rsp.json["id"]
        self.assertIsNotNone(user_id)
        mock_noti.push_for_user.asser_called_once()

        rsp = self.flask_client.get(
            f"{self.base_path}/{self.user_id}",
            headers=self.headers_for_user,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(new_care_plan_group_id, rsp.json["carePlanGroupId"])

    @patch(NOTIFICATION_PATH)
    def test_success_update_user_care_plan_group_by_custom_role_with_manage_patient(
        self, mock_noti
    ):
        headers = self.get_headers_for_token(VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT)
        new_care_plan_group_id = "com.huma.covid19.severe"
        data = {"carePlanGroupId": new_care_plan_group_id, "note": ""}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/deployment/{self.deployment_id}/care-plan-group",
            headers=headers,
            json=data,
        )
        self.assertEqual(rsp.status_code, 200)
        user_id = rsp.json["id"]
        self.assertIsNotNone(user_id)
        mock_noti.push_for_user.asser_called_once()

        rsp = self.flask_client.get(
            f"{self.base_path}/{self.user_id}",
            headers=self.headers_for_user,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(new_care_plan_group_id, rsp.json["carePlanGroupId"])

    @patch(NOTIFICATION_PATH, MagicMock())
    def test_failure_update_user_care_plan_group_by_custom_role_with_out_manage_patient(
        self,
    ):
        headers = self.get_headers_for_token(
            VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
        )
        new_care_plan_group_id = "com.huma.covid19.severe"
        data = {"carePlanGroupId": new_care_plan_group_id, "note": ""}
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{self.user_id}/deployment/{self.deployment_id}/care-plan-group",
            headers=headers,
            json=data,
        )
        self.assertEqual(rsp.status_code, 403)

    @patch(NOTIFICATION_PATH, MagicMock())
    def test_update_user_care_plan_group_key_actions_removed(self):
        code = DEPLOYMENT_X_USER_CODE + DEPLOYMENT_X_EXTENSION_ACTIVATION_CODE_2
        user_data = get_sign_up_data("user2@example.com", "user2", code)
        user_id = self.register_user(user_data)

        start_events_count = self.events_count(user_id)

        new_care_plan_group_id = MILD_GROUP
        data = {"carePlanGroupId": new_care_plan_group_id, "note": ""}
        rsp = self.flask_client.post(
            f"{self.base_path}/{user_id}/deployment/{self.deployment_id}/care-plan-group",
            headers=self.headers_for_manager,
            json=data,
        )
        self.assertEqual(rsp.status_code, 200)
        end_events_count = self.events_count(user_id)
        self.assertGreater(start_events_count, end_events_count)

    def test_retrieve_user_configuration_with_only_valid_data(self):
        headers = self.get_headers_for_token(self.user_with_invalid_module_config_id)
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{self.user_with_invalid_module_config_id}/configuration",
            headers=headers,
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertIn(Deployment.MODULE_CONFIGS, rsp.json)
        self.assertEqual(8, len(rsp.json[Deployment.MODULE_CONFIGS]))
        self.assertIn(Deployment.KEY_ACTIONS, rsp.json)
        key_actions: list[dict] = rsp.json[Deployment.KEY_ACTIONS]
        self.assertEqual(2, len(key_actions))
        for key_action in key_actions:
            self.assertNotEqual(key_action["id"], OBSERVATION_NOTE_ID)

    def test_failure_retrieve_user_configuration_invalid_care_plan_group_id(self):
        headers = self.get_headers_for_token(self.user_with_invalid_care_plan_group_id)
        rsp = self.flask_client.get(
            f"{self.base_path}/{self.user_with_invalid_care_plan_group_id}/configuration",
            headers=headers,
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(100003, rsp.json["code"])
