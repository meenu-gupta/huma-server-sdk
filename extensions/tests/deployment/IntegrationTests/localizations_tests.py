from pathlib import Path
from jsonpatch import make_patch

from extensions.deployment.models.deployment import Deployment, Reason
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
)
from sdk.common.localization.utils import Language
from tools.mongodb_script.update_offboarding_reasons_localization import (
    update_offboarding_localizations,
)

USER_ID = "5e8f0c74b50aa9656c34789c"
SAMPLE_LOCALIZATIONS = {
    "en": {
        "hu_deployment_name": "deployment 1",
        "hu_consent_sections_0_details": "The following screens explain how Medopad works, the data it collects and privacy.",
        "hu_consent_sections_0_reviewDetails": "Medopad helps to share",
        "hu_BloodPressure_moduleName": "BloodPressure Module",
        "hu_BloodPressure_schedule_friendlyText": "Please input your weight.",
        "hu_BloodPressure_shortModuleName": "BM",
    },
    "de": {
        "hu_deployment_name": "Bereitstellung 1",
        "hu_consent_sections_0_details": "In den folgenden Bildschirmen werden die Funktionsweise von Medopad, die gesammelten Daten und der Datenschutz erläutert.",
        "hu_consent_sections_0_reviewDetails": "Medopad hilft beim Teilen",
        "hu_BloodPressure_moduleName": "BloodPressure-Modul",
        "hu_BloodPressure_schedule_friendlyText": "Bitte geben Sie Ihr Gewicht ein.",
        "hu_BloodPressure_shortModuleName": "BM DE",
    },
}


LOCALIZATION_RESULT = {
    "deploymentId": "5d386cc6ff885918d96edb2c",
    "name": "Deployment1",
    "description": "Deployment Description",
    "status": "DRAFT",
    "color": "0x007AFF",
    "code": "Deployment code",
    "userActivationCode": "53924415",
    "managerActivationCode": "17781957",
    "proxyActivationCode": "96557443",
    "moduleConfigs": [
        {
            "moduleName": "BloodPressure ModuleName",
            "shortModuleName": "BloodPressure shortModuleName",
            "schedule": {"friendlyText": "BloodPressure schedule friendly text"},
        }
    ],
    "learn": {
        "sections": [
            {
                "title": "Test section",
                "articles": [
                    {
                        "title": "Article 0",
                        "content": {"textDetails": "Here what you read"},
                    }
                ],
            }
        ]
    },
    "keyActions": [
        {
            "title": "PAM Questionnaire",
            "description": "You have a new activity for the DeTAP study. Please complete as soon as you are able to.",
        }
    ],
    "extraCustomFields": {
        "mediclinicNumber": {
            "errorMessage": "Insurance Number is incorrect",
            "onboardingCollectionText": "Please enter mediclinic number",
            "profileCollectionText": "Patient Unique ID",
        }
    },
    "features": {
        "messaging": {
            "messages": [
                "Great job! Keep up the good work.",
                "You're doing great!",
                "Awesome – you're right on track with your targets.",
                "Excellent work",
                "You're close to completing your tasks, keep going.",
            ]
        }
    },
    "stats": {"completedCount": {"unit": "state unit"}},
    "icon": {"key": "deployment/5d386cc6ff885918d96edb2c/sample.png"},
    "updateDateTime": "2020-04-09T11:53:37.042000Z",
    "roles": [{"name": "Custom Role", "permissions": ["VIEW_PATIENT_IDENTIFIER"]}],
    "localizations": {
        "en": {"hu_BloodPressure_moduleName": "BloodPressure ModuleName"}
    },
}


class LocalizationsTestCase(AbstractDeploymentTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.deployment_route = "/api/extensions/v1beta/deployment"
        cls.user_route = "/api/extensions/v1beta/user"

    def _update_localizations(self, body=None):
        if body is None:
            body = SAMPLE_LOCALIZATIONS
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{self.deployment_id}/update-localizations",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

    def _get_deployment(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def test_success_deployment_update_dt_gets_updated(self):
        deployment = self._get_deployment()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        self._update_localizations()

        deployment = self._get_deployment()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_success_retrieve_user_language_specified_configuration(self):
        body = SAMPLE_LOCALIZATIONS
        self._update_localizations(body)
        headers_user = self.get_headers_for_token(USER_ID)
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/configuration", headers=headers_user
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body["de"]["hu_deployment_name"], rsp.json["name"])
        self.assertEqual(
            body["de"]["hu_consent_sections_0_details"],
            rsp.json["consent"]["sections"][0]["details"],
        )
        self.assertEqual(
            body["de"]["hu_consent_sections_0_reviewDetails"],
            rsp.json["consent"]["sections"][0]["reviewDetails"],
        )
        self.assertEqual(
            body["de"]["hu_BloodPressure_moduleName"],
            rsp.json["moduleConfigs"][0]["moduleName"],
        )
        self.assertEqual(
            body["de"]["hu_BloodPressure_schedule_friendlyText"],
            rsp.json["moduleConfigs"][0]["schedule"]["friendlyText"],
        )
        self.assertEqual(
            body["de"]["hu_BloodPressure_shortModuleName"],
            rsp.json["moduleConfigs"][0]["shortModuleName"],
        )

    def test_success_retrieve_default_language_specified_configuration(self):
        body = SAMPLE_LOCALIZATIONS
        self._update_localizations(body)
        headers_user = self.get_headers_for_token(USER_ID)
        headers_user["x-hu-locale"] = "fr"
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/configuration", headers=headers_user
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body["en"]["hu_deployment_name"], rsp.json["name"])
        self.assertEqual(
            body["en"]["hu_consent_sections_0_details"],
            rsp.json["consent"]["sections"][0]["details"],
        )
        self.assertEqual(
            body["en"]["hu_consent_sections_0_reviewDetails"],
            rsp.json["consent"]["sections"][0]["reviewDetails"],
        )
        self.assertEqual(
            body["en"]["hu_BloodPressure_moduleName"],
            rsp.json["moduleConfigs"][0]["moduleName"],
        )
        self.assertEqual(
            body["en"]["hu_BloodPressure_schedule_friendlyText"],
            rsp.json["moduleConfigs"][0]["schedule"]["friendlyText"],
        )
        self.assertEqual(
            body["en"]["hu_BloodPressure_shortModuleName"],
            rsp.json["moduleConfigs"][0]["shortModuleName"],
        )

    def test_success_retrieve_default_language_specified_configuration_with_invalid_lang(
        self,
    ):
        body = SAMPLE_LOCALIZATIONS
        self._update_localizations(body)
        headers_user = self.get_headers_for_token(USER_ID)
        headers_user["x-hu-locale"] = "invalid-lang"
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/configuration", headers=headers_user
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body["en"]["hu_deployment_name"], rsp.json["name"])

    def test_offboarding_reason_localization_configuration(self):
        headers = self.get_headers_for_token(USER_ID)
        headers["x-hu-locale"] = Language.DE_DE
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/configuration", headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        reasons = rsp.json["features"]["offBoardingReasons"]["reasons"]
        self.assertEqual("Behandlung abgeschlossen", reasons[0][Reason.DISPLAY_NAME])
        self.assertEqual("Verstorben", reasons[1][Reason.DISPLAY_NAME])

    def test_update_offboarding_localizations(self):
        user_id = "5eda5e367adadfb46f7ff71f"  # from deployment with default reasons
        headers = self.get_headers_for_token(user_id)
        headers["x-hu-locale"] = Language.DE_DE
        initial_config_rsp = self.flask_client.get(
            f"{self.user_route}/{user_id}/configuration", headers=headers
        )
        reasons = initial_config_rsp.json["features"]["offBoardingReasons"]["reasons"]
        self.assertEqual("Completed treatment", reasons[0][Reason.DISPLAY_NAME])

        default_reasons = Reason._default_reasons()
        update_offboarding_localizations(self.mongo_database, default_reasons)

        updated_config_rsp = self.flask_client.get(
            f"{self.user_route}/{user_id}/configuration", headers=headers
        )
        updated_reasons = updated_config_rsp.json["features"]["offBoardingReasons"][
            "reasons"
        ]
        self.assertEqual(6, len(updated_reasons))
        self.assertEqual(
            "Behandlung abgeschlossen", updated_reasons[0][Reason.DISPLAY_NAME]
        )
        self.assertEqual("Verstorben", updated_reasons[1][Reason.DISPLAY_NAME])


class LocalizationsFullTestCase(AbstractDeploymentTestCase):
    fixtures = [Path(__file__).parent.joinpath("fixtures/localizations_test_dump.json")]
    headers_user: None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_route = "/api/extensions/v1beta/user"
        cls.headers_user = cls.get_headers_for_token(USER_ID)

    def test_success_configuration_translated(self):
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/configuration", headers=self.headers_user
        )
        self.assertEqual(200, rsp.status_code)
        patch = make_patch(LOCALIZATION_RESULT, rsp.json)
        self.assertEqual(
            len(list(filter(lambda d: d["op"] == "replace", patch.patch))), 0
        )

    def test_success_full_configuration_translated(self):
        rsp = self.flask_client.get(
            f"{self.user_route}/{USER_ID}/fullconfiguration", headers=self.headers_user
        )
        self.assertEqual(200, rsp.status_code)
        patch = make_patch(LOCALIZATION_RESULT, rsp.json["deployments"][0])
        self.assertEqual(
            len(list(filter(lambda d: d["op"] == "replace", patch.patch))), 0
        )
