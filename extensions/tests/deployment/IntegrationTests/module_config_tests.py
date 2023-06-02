from copy import copy
from extensions.deployment.service.deployment_service import LocalizationKeys


from extensions.module_result.models.module_config import Footnote, ModuleConfig
from extensions.module_result.models.primitives import (
    AZGroupKeyActionTrigger,
    AZFurtherPregnancyKeyActionTrigger,
)
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
)
from extensions.tests.deployment.IntegrationTests.test_helpers import (
    get_module_config_by_id,
    get_sample_pam_questionnaire,
    get_sample_promis_pain_questionnaire,
    get_sample_questionnaire_with_trademark_text,
    module_config_with_config_body,
    simple_module_config,
    simple_module_config_not_requiring_default_disclaimer_config,
    simple_module_config_requiring_default_disclaimer_config,
)
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Localization
from sdk.common.utils import inject
from sdk.common.utils.validators import utc_str_field_to_val

VALID_MANAGER_ID = "60071f359e7e44330f732037"
VALID_USER_ID = "5e8f0c74b50aa9656c34789c"


class ModuleConfigTestCase(AbstractDeploymentTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.create_or_update_url = (
            f"{cls.deployment_route}/deployment/{cls.deployment_id}/module-config"
        )
        cls.createModuleConfigBody = simple_module_config()
        cls.user_config_url = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/configuration"
        )
        default_disclaimer_text_key = LocalizationKeys.DEFAULT_DISCLAIMER_TEXT
        localization = inject.instance(Localization)
        default_localization = localization.get("en")
        cls.default_disclaimer_text = default_localization.get(
            default_disclaimer_text_key
        )

    def test_module_config_creation(self):
        body = copy(self.createModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_module_config_creation_eq5(self):
        body = {
            "moduleId": "EQ5D5L",
            "moduleName": "hu_eq5d5l_modulename",
            "ragThresholds": [],
            "shortModuleName": "EQ5D",
            "schedule": {
                "friendlyText": "AS NEEDED",
                "timesOfDay": [],
                "timesPerDuration": 0,
            },
            "notificationData": {
                "title": "hu_eq5d5l_notification_title",
                "body": "hu_eq5d5l_notification_body",
            },
            "status": "ENABLED",
            "about": "hu_eq5d5l_about",
            "order": 4,
            "configBody": {
                "toggleIndexValue": True,
                "id": "hu_eq5d5l_configbody",
                "isForManager": False,
                "publisherName": "MZ",
                "questionnaireName": "hu_eq5d5l_moduleName",
                "name": "EQ-5D-5L",
                "questionnaireId": "eq5d5l_module",
                "trademarkText": "hu_eq5d5l_trademark",
                "region": "UK",
                "isHorizontalFlow": True,
            },
        }
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_group_trigger_module_config_creation(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.MODULE_ID] = AZGroupKeyActionTrigger.__name__
        body[ModuleConfig.CONFIG_BODY] = {
            "keyActions": {
                "PREGNANT": ["InfantFollowUp"],
                "BREAST_FEEDING": ["PregnancyUpdate"],
                "BOTH_P_AND_B": ["InfantFollowUp"],
                "FEMALE_LESS_50_NOT_P_OR_B": ["PregnancyUpdate"],
                "MALE_OR_FEMALE_OVER_50": ["AdditionalQoL"],
            }
        }
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_trigger_module_config_creation(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.MODULE_ID] = AZGroupKeyActionTrigger.__name__
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code, rsp.json)

    def test_failure_trigger_module_config_creation_invalid_config_body(self):
        body = copy(self.createModuleConfigBody)
        modules = [
            AZGroupKeyActionTrigger.__name__,
            AZFurtherPregnancyKeyActionTrigger.__name__,
        ]

        for module_id in modules:
            body[ModuleConfig.MODULE_ID] = module_id
            body[ModuleConfig.CONFIG_BODY] = None
            rsp = self.flask_client.post(
                self.create_or_update_url, json=body, headers=self.headers
            )
            self.assertEqual(400, rsp.status_code, rsp.json)

    def test_failure_trigger_module_config_creation_missing_keys(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.MODULE_ID] = AZGroupKeyActionTrigger.__name__
        body[ModuleConfig.CONFIG_BODY] = {"keyActions": {}}
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_pregnancy_trigger_module_config_creation(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.MODULE_ID] = AZFurtherPregnancyKeyActionTrigger.__name__
        body[ModuleConfig.CONFIG_BODY] = {
            "keyActions": {"PREGNANT": ["InfantFollowUp"], "NOT_PREGNANT": []}
        }
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_pregnancy_trigger_module_config_creation(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.MODULE_ID] = AZFurtherPregnancyKeyActionTrigger.__name__
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_pregnancy_trigger_module_config_creation_missing_keys(self):
        body = copy(self.createModuleConfigBody)
        body[ModuleConfig.CONFIG_BODY] = {"keyActions": {}}
        body[ModuleConfig.MODULE_ID] = AZFurtherPregnancyKeyActionTrigger.__name__
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_module_config_update(self):
        body = copy(self.createModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        module_config_id = rsp.json["id"]

        deployment = self.get_deployment()
        old_config = get_module_config_by_id(deployment, module_config_id)

        body.update({"about": "New test about.", "id": module_config_id})
        rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment()
        new_config = get_module_config_by_id(deployment, module_config_id)
        self.assertNotEqual(new_config["about"], old_config["about"])
        old_update_datetime = utc_str_field_to_val(old_config["updateDateTime"])
        new_update_datetime = utc_str_field_to_val(new_config["updateDateTime"])
        self.assertGreater(new_update_datetime, old_update_datetime)

        body.update({"about": "Newer test about .", "id": module_config_id})
        rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment()
        new_config = get_module_config_by_id(deployment, module_config_id)
        self.assertNotEqual(new_config["about"], old_config["about"])

        old_update_datetime = utc_str_field_to_val(old_config["updateDateTime"])
        new_update_datetime = utc_str_field_to_val(new_config["updateDateTime"])
        self.assertGreater(new_update_datetime, old_update_datetime)

    def test_create_module_config_with_config_body(self):
        body = module_config_with_config_body()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_create_and_update_module_config_with_export_short_code(self):
        body = module_config_with_config_body()
        body["configBody"]["pages"][0]["items"][0]["exportShortCode"] = "test"

        # 1. Creation
        created_rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, created_rsp.status_code)
        # 2. Failed duplicate creation
        failed_create_rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, failed_create_rsp.status_code)
        # 3. Failed duplicate update
        module_config_id = created_rsp.json[ModuleConfig.ID]
        body[ModuleConfig.ID] = module_config_id
        failed_update_rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, failed_update_rsp.status_code)
        # 4. Updated with new unique value
        body["configBody"]["pages"][0]["items"][0]["exportShortCode"] = "test2"
        updated_rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(200, updated_rsp.status_code)

    def test_create_module_config_with_invalid_option_value(self):
        invalid_option = {"label": "None", "value": 1, "weight": 1}
        body = module_config_with_config_body(invalid_option)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_create_module_config_with_no_option(self):
        body = module_config_with_config_body()
        body["configBody"]["pages"][0]["items"][0]["options"] = None
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        body["configBody"]["pages"][0]["items"][0]["options"] = []
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_create_and_update_module_config_with_with_no_option(self):
        body = module_config_with_config_body()

        # 1. Creation
        created_rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, created_rsp.status_code)

        # 2. Updated with options as None
        body["configBody"]["pages"][0]["items"][0]["options"] = None
        updated_rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, updated_rsp.status_code)
        # 3. Updated with options as an empty list
        body["configBody"]["pages"][0]["items"][0]["options"] = []
        updated_rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, updated_rsp.status_code)

    def test_module_config_creation_with_date(self):
        body = copy(self.createModuleConfigBody)
        body["createDateTime"] = "2020-04-07T17:05:51"
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_module_config_creation_for_not_existing_deployment(self):
        body = copy(self.createModuleConfigBody)
        deployment_id = "5d386cc6ff885918d96edb5c"
        create_or_update_url = (
            f"{self.deployment_route}/deployment/{deployment_id}/module-config"
        )
        rsp = self.flask_client.post(
            create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_module_config_retrieve_and_change_footnote(self):
        body = module_config_with_config_body()

        # 1. Creation
        created_rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, created_rsp.status_code)

        # 2. Updated with enabled changed to false
        body["footnote"]["enabled"] = True
        updated_rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(200, updated_rsp.status_code)

        # 3. Retrieve
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json["moduleConfigs"]:
            if mc["moduleId"] == body["moduleId"]:
                result_footnote = mc["footnote"]
        self.assertEqual(True, result_footnote["enabled"])

    def test_module_config_apply_default_disclaimer_config_when_footnote_is_missing(
        self,
    ):
        body = simple_module_config_requiring_default_disclaimer_config()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json["moduleConfigs"]:
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertEqual(True, module_footnote.get("enabled"))
        self.assertEqual(
            self.default_disclaimer_text, module_footnote.get(Footnote.TEXT)
        )

    def test_module_config_skip_applying_default_disclaimer_config_for_excluded_modules(
        self,
    ):
        body = simple_module_config_not_requiring_default_disclaimer_config()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertIsNone(module_footnote)

    def test_module_config_skip_applying_default_disclaimer_config_when_trademark_text_is_available(
        self,
    ):
        body = get_sample_questionnaire_with_trademark_text()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertIsNone(module_footnote)

    def test_module_config_skip_applying_default_disclaimer_config_for_excluded_questionnaire_types(
        self,
    ):
        body = get_sample_promis_pain_questionnaire()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertIsNone(module_footnote)

    def test_module_config_skip_applying_default_disclaimer_config_to_pam_questionnaires(
        self,
    ):
        body = get_sample_pam_questionnaire()
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertIsNone(module_footnote)

    def test_module_config_apply_default_disclaimer_config_when_footnote_text_is_missing(
        self,
    ):
        body = simple_module_config_requiring_default_disclaimer_config()
        body[ModuleConfig.FOOTNOTE] = {Footnote.ENABLED: True}
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertEqual(True, module_footnote.get("enabled"))
        self.assertEqual(
            self.default_disclaimer_text, module_footnote.get(Footnote.TEXT)
        )

    def test_module_config_apply_default_disclaimer_config_when_footnote_text_is_empty(
        self,
    ):
        body = simple_module_config_requiring_default_disclaimer_config()
        body[ModuleConfig.FOOTNOTE] = {Footnote.ENABLED: True, Footnote.TEXT: ""}
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertEqual(True, module_footnote.get("enabled"))
        self.assertEqual(
            self.default_disclaimer_text, module_footnote.get(Footnote.TEXT)
        )

    def test_module_config_skip_applying_default_disclaimer_config_when_footnote_is_disabled(
        self,
    ):
        body = simple_module_config_requiring_default_disclaimer_config()
        footnote_text = "sample footnote text"
        body[ModuleConfig.FOOTNOTE] = {
            Footnote.ENABLED: False,
            Footnote.TEXT: footnote_text,
        }
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_config_url,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        for mc in rsp.json.get("moduleConfigs"):
            if mc.get("moduleId") == body.get("moduleId"):
                module_footnote = mc.get("footnote")
        self.assertFalse(module_footnote.get(Footnote.ENABLED))
        self.assertEqual(footnote_text, module_footnote.get(Footnote.TEXT))

    def test_modules_retrieve(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/modules", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertNotEqual(0, len(rsp.json))

    def test_module_config_delete(self):
        deployment = self.get_deployment()
        old_key_actions_count = len(deployment["keyActions"])

        url = f"{self.deployment_route}/deployment/{self.deployment_id}/module-config/5e94b2007773091c9a592650"
        rsp = self.flask_client.delete(url, headers=self.headers)
        self.assertEqual(204, rsp.status_code)

        deployment = self.get_deployment()
        new_key_action_count = len(deployment["keyActions"])
        self.assertLess(new_key_action_count, old_key_actions_count)

    def test_deployment_revision_after_module_config_creation(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        old_version = rsp.json["version"]
        body = copy(self.createModuleConfigBody)

        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        new_version = rsp.json["version"]
        self.assertEqual(old_version + 1, new_version)

    def test_deployment_revision_after_module_config_update(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        old_version = rsp.json["version"]

        body = copy(self.createModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(old_version + 1, rsp.json["version"])
        old_version = rsp.json["version"]

        body[ModuleConfig.ID] = "5e94b2007773091c9a592650"
        rsp = self.flask_client.put(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(old_version + 1, rsp.json["version"])
