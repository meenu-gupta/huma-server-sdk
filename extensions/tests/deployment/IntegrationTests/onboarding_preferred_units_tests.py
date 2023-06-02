from pathlib import Path
from unittest import mock
from unittest.mock import PropertyMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.authorization.boarding.preferred_units_module import (
    PreferredUnitsModule,
)
from extensions.organization.component import OrganizationComponent
from extensions.tests.shared.test_helpers import simple_preferred_units
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

DEFAULT_MODULES_PATH = (
    "extensions.authorization.boarding.manager.BoardingManager.default_modules"
)
USER_ID = "60642e821668fbf7381eefa0"


class OnboardingPreferredUnitsTestCase(ExtensionTestCase):
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
        super(OnboardingPreferredUnitsTestCase, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(USER_ID)

    def test_success_user_update_profile_should_be_unprotected(self):
        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (PreferredUnitsModule,)

            url = f"/api/extensions/v1beta/user/{USER_ID}"

            json = {User.HEIGHT: 180}

            rsp = self.flask_client.post(
                url,
                json=json,
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 200)

    def test_success_route_protection_onboarding_preferred_units(self):
        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (PreferredUnitsModule,)

            rsp = self.flask_client.get(
                f"/api/extensions/v1beta/user/{USER_ID}/fullconfiguration",
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 428)

    def test_success_submit_preferred_units(self):
        with mock.patch(
            DEFAULT_MODULES_PATH, new_callable=PropertyMock
        ) as mock_default_modules:
            mock_default_modules.return_value = (PreferredUnitsModule,)

            rsp = self.flask_client.post(
                f"/api/extensions/v1beta/user/{USER_ID}",
                json=simple_preferred_units(),
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 200)

            rsp = self.flask_client.get(
                f"/api/extensions/v1beta/user/{USER_ID}/fullconfiguration",
                headers=self.headers,
            )
            self.assertEqual(rsp.status_code, 200)
