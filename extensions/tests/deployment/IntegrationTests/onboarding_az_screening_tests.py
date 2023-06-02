from pathlib import Path
from unittest import mock
from unittest.mock import PropertyMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.router.user_profile_response import (
    RetrieveDeploymentConfigResponseObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.boarding.az_screening_module import AZPScreeningModule
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import AZScreeningQuestionnaire
from extensions.module_result.modules import AZScreeningQuestionnaireModule
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_az_screening,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

USER_ID = "60642e821668fbf7381eefa0"
VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
PRESCREENING_ONBOARDING_MODULE_ID = "606705adc7558713d7d398e8"

DEFAULT_MODULES_PATH = (
    "extensions.authorization.boarding.manager.BoardingManager.default_modules"
)

MODULE_RESULT_ROUTE = f"/api/extensions/v1beta/user/{USER_ID}/module-result"


class OnboardingAZScreeningTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
    ]
    override_config = {
        "server.deployment.enableAuthz": "true",
        "server.deployment.onBoarding": "true",
    }

    @classmethod
    def setUpClass(cls) -> None:
        super(OnboardingAZScreeningTestCase, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(USER_ID)

    def get_user_configuration(self):
        url = f"/api/extensions/v1beta/user/{USER_ID}/configuration"
        return self.flask_client.get(url, headers=self.headers)

    def test_success_module_result_route_should_be_unprotected(self):
        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (AZPScreeningModule,)

            url = f"{MODULE_RESULT_ROUTE}/{AZScreeningQuestionnaireModule.moduleId}"

            rsp = self.flask_client.post(
                url,
                json=[sample_az_screening()],
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 201)

    def test_success_user_passed_az_screening(self):
        next_onboarding_task_name = (
            RetrieveDeploymentConfigResponseObject.NEXT_ONBOARDING_TASK_ID
        )

        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (AZPScreeningModule,)

            # should result with PRESCREENING_ONBOARDING_MODULE_ID id as a next onboarding task
            rsp = self.get_user_configuration()
            self.assertEqual(rsp.status_code, 200)
            self.assertEqual(
                rsp.json[next_onboarding_task_name],
                PRESCREENING_ONBOARDING_MODULE_ID,
            )

            # creating AZScreeningQuestionnaire for user
            url = f"{MODULE_RESULT_ROUTE}/{AZScreeningQuestionnaireModule.moduleId}"
            rsp = self.flask_client.post(
                url,
                json=[sample_az_screening()],
                headers=self.headers,
            )
            self.assertEqual(201, rsp.status_code)

            # now next onboarding task shouldn't appear in configuration
            rsp = self.get_user_configuration()
            self.assertNotIn(next_onboarding_task_name, rsp.json)

    def test_failure_module_result_user_should_be_offboarded(self):
        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (AZPScreeningModule,)
            url = f"{MODULE_RESULT_ROUTE}/{AZScreeningQuestionnaireModule.moduleId}"
            az_data = sample_az_screening()
            az_data[
                AZScreeningQuestionnaire.HAS_RECEIVED_COVID_VAC_IN_PAST_4_WEEKS
            ] = False
            rsp = self.flask_client.post(
                url,
                json=[az_data],
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 412)

            rsp = self.get_user_configuration()
            self.assertTrue(rsp.json["isOffBoarded"])
