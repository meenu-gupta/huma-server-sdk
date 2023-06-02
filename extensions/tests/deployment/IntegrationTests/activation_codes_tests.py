from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import Deployment, Security
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
DEPLOYMENT_COLLECTION = "deployment"


class ActivationTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/activation_code_deployment.json")
    ]
    override_config = {
        "server.deployment.enableAuthz": "true",
    }
    ACTIVATION_KEY_FOR_NO_SECURITY_DEPLOYMENT = "96557443"
    ACTIVATION_KEY_FOR_SECURITY_DEPLOYMENT = "96557444"
    ACTIVATION_KEY_FOR_DEPRECATED_MFA_DEPLOYMENT = "96557445"

    @classmethod
    def setUpClass(cls) -> None:
        super(ActivationTestCase, cls).setUpClass()
        cls.deployment_route = "/api/extensions/v1beta"
        cls.section_id = "5e946c69e8002eac4a107f56"

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(VALID_USER_ID)

    def test_check_activation_code(self):
        get_rsp = self.flask_client.get(
            f"/api/public/v1beta/activation-code/{self.ACTIVATION_KEY_FOR_NO_SECURITY_DEPLOYMENT}",
            headers=self.headers,
        )
        self.assertEqual(201, get_rsp.status_code)

    def test_check_activation_code_for_security_enabled_deployment(self):
        get_rsp = self.flask_client.get(
            f"/api/public/v1beta/activation-code/{self.ACTIVATION_KEY_FOR_SECURITY_DEPLOYMENT}",
            headers=self.headers,
        )
        self.assertEqual(201, get_rsp.status_code)
        self.assertEqual(get_rsp.json[Deployment.SECURITY][Security.MFA_REQUIRED], True)
        self.assertEqual(
            get_rsp.json[Deployment.SECURITY][Security.APP_LOCK_REQUIRED], False
        )

    def test_check_activation_code_for_deprecated_mfarequired_deployment(self):
        get_rsp = self.flask_client.get(
            f"/api/public/v1beta/activation-code/{self.ACTIVATION_KEY_FOR_DEPRECATED_MFA_DEPLOYMENT}",
            headers=self.headers,
        )
        self.assertEqual(201, get_rsp.status_code)
        self.assertEqual(get_rsp.json[Security.MFA_REQUIRED], False)
        self.assertEqual(
            get_rsp.json[Deployment.SECURITY][Security.MFA_REQUIRED], False
        )
        self.assertEqual(
            get_rsp.json[Deployment.SECURITY][Security.APP_LOCK_REQUIRED], False
        )
