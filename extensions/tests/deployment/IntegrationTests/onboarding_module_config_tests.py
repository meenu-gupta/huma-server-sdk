from copy import copy

from bson import ObjectId

from extensions.deployment.models.deployment import (
    Deployment,
    OnboardingModuleConfig,
    DeploymentRevision,
)
from extensions.deployment.models.status import EnableStatus
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
)

VALID_MANAGER_ID = "60071f359e7e44330f732037"
USER_ID = "5ffee8a004ae8ffa8e721114"


def simple_onboarding_module_config() -> dict:
    return {
        OnboardingModuleConfig.ONBOARDING_ID: "Consent",
        OnboardingModuleConfig.STATUS: EnableStatus.ENABLED.name,
        OnboardingModuleConfig.ORDER: 1,
        OnboardingModuleConfig.CONFIG_BODY: {},
    }


def get_onboarding_module_config_by_id(
    deployment: dict, onboarding_module_config_id: str
):
    return next(
        filter(
            lambda x: x["id"] == onboarding_module_config_id,
            deployment[Deployment.ONBOARDING_CONFIGS],
        )
    )


class OnboardingModuleConfigTestCase(AbstractDeploymentTestCase):
    deployment_route: str
    DEPLOYMENT_REVISION_COLLECTION = "deploymentrevision"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.create_or_update_url = f"{cls.deployment_route}/deployment/{cls.deployment_id}/onboarding-module-config"
        cls.createOnboardingModuleConfigBody = simple_onboarding_module_config()
        cls.user_headers = cls.get_headers_for_token(USER_ID)

    def test_onboarding_module_config_creation(self):
        body = copy(self.createOnboardingModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_onboarding_module_config_creation_without_exist_config(self):
        self.remove_onboarding()
        body = copy(self.createOnboardingModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def test_onboarding_module_config_creation_for_not_existing_deployment(self):
        body = copy(self.createOnboardingModuleConfigBody)
        deployment_id = "5d386cc6ff885918d96edb5c"
        create_or_update_url = f"{self.deployment_route}/deployment/{deployment_id}/onboarding-module-config"
        rsp = self.flask_client.post(
            create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def _get_deployment(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def test_deployment_revision_after_onboarding_module_config_creation(self):
        deployment = self._get_deployment()
        old_version = deployment[Deployment.VERSION]
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]
        body = copy(self.createOnboardingModuleConfigBody)

        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        onboarding_config_id = rsp.json[OnboardingModuleConfig.ID]
        deployment = self._get_deployment()
        new_version = deployment[Deployment.VERSION]

        self.assertEqual(old_version + 1, new_version)
        self.assertNotEquals(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

        # update once again to see date changes on update
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]
        rsp = self.flask_client.post(
            self.create_or_update_url,
            json={**body, OnboardingModuleConfig.ID: onboarding_config_id},
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        deployment = self._get_deployment()
        self.assertNotEquals(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_deployment_revision_has_object_ids(self):
        body = copy(self.createOnboardingModuleConfigBody)

        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        data = self.mongo_database[self.DEPLOYMENT_REVISION_COLLECTION].find_one(
            {DeploymentRevision.DEPLOYMENT_ID: ObjectId(self.deployment_id)}
        )
        self.assertIsInstance(data.get(DeploymentRevision.SUBMITTER_ID), ObjectId)
        self.assertIsInstance(
            data.get(DeploymentRevision.ONBOARDING_CONFIG_ID), ObjectId
        )

    def test_deployment_revision_after_module_config_update(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        old_version = rsp.json["version"]

        body = copy(self.createOnboardingModuleConfigBody)
        rsp = self.flask_client.post(
            self.create_or_update_url, json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        inserted_id = rsp.json[OnboardingModuleConfig.ID]

        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(old_version + 1, rsp.json["version"])
        old_version = rsp.json["version"]
        body[OnboardingModuleConfig.ID] = inserted_id
        body[OnboardingModuleConfig.ORDER] = 8

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
        # checking default values
        self.assertEqual(rsp.json["onboardingConfigs"][5]["userTypes"], ["User"])

    def test_onboarding_module_config_delete(self):
        url = f"{self.deployment_route}/deployment/{self.deployment_id}/module-config/604c89573a295dad259abb03"
        rsp = self.flask_client.delete(url, headers=self.headers)
        self.assertEqual(204, rsp.status_code)
