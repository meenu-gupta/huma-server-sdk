from pathlib import Path
from unittest import mock
from unittest.mock import PropertyMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.router.user_profile_response import (
    RetrieveDeploymentConfigResponseObject,
)
from extensions.deployment.boarding.helper_agreement_module import HelperAgreementModule
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

PROXY_USER_ID = "606eba3a2c94383d620b52ad"
REGULAR_USER_ID = "60642e821668fbf7381eefa0"
VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
HELPER_AGREEMENT_ONBOARDING_MODULE_ID = "606ea61c5d52b6ec29d02dac"

DEFAULT_MODULES_PATH = (
    "extensions.authorization.boarding.manager.BoardingManager.default_modules"
)
ROOT_URL = "/api/extensions/v1beta"


class OnboardingHelperAgreementTestCase(ExtensionTestCase):
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
    }

    @classmethod
    def setUpClass(cls) -> None:
        super(OnboardingHelperAgreementTestCase, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(PROXY_USER_ID)

    def get_user_configuration(self, user_id=PROXY_USER_ID):
        url = f"{ROOT_URL}/user/{user_id}/configuration"
        rsp = self.flask_client.get(
            url,
            headers=self.get_headers_for_token(user_id),
        )
        return rsp

    def test_success_proxy_user_pass_helper_agreement(self):
        next_onboarding_task_name = (
            RetrieveDeploymentConfigResponseObject.NEXT_ONBOARDING_TASK_ID
        )

        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:

            mock_default_modules.return_value = (HelperAgreementModule,)
            rsp = self.get_user_configuration()
            self.assertEqual(rsp.status_code, 200)
            self.assertEqual(
                rsp.json[next_onboarding_task_name],
                HELPER_AGREEMENT_ONBOARDING_MODULE_ID,
            )

            # creating a helper agreement log
            url = f"{ROOT_URL}/user/{PROXY_USER_ID}/deployment/{VALID_DEPLOYMENT_ID}/helperagreementlog"
            rsp = self.flask_client.post(
                url,
                json={
                    HelperAgreementLog.STATUS: HelperAgreementLog.Status.AGREE_AND_ACCEPT.value
                },
                headers=self.headers,
            )
            self.assertEqual(201, rsp.status_code)

            # now next onboarding task shouldn't appear in configuration
            rsp = self.get_user_configuration()
            self.assertNotIn(next_onboarding_task_name, rsp.json)
