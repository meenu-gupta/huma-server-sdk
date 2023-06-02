from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.inbox.component import InboxComponent
from sdk.notification.component import NotificationComponent
from sdk.versioning.component import VersionComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
DEPLOYMENT_COLLECTION = "deployment"


class AbstractDeploymentTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        NotificationComponent(),
        InboxComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        CalendarComponent(),
        KeyActionComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    override_config = {"server.deployment.enableAuthz": "true"}

    @classmethod
    def setUpClass(cls) -> None:
        super(AbstractDeploymentTestCase, cls).setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.deployment_route = "/api/extensions/v1beta"
        cls.section_id = "5e946c69e8002eac4a107f56"

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(VALID_USER_ID)

    def get_deployment(self, deployment_id=None) -> dict:
        if not deployment_id:
            deployment_id = self.deployment_id

        deployment_url = f"{self.deployment_route}/deployment/{deployment_id}"
        rsp = self.flask_client.get(deployment_url, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def remove_onboarding(self):
        self.mongo_database[DEPLOYMENT_COLLECTION].update_one(
            {"_id": ObjectId(self.deployment_id)},
            {"$unset": {"onboardingConfigs": 1}},
        )

    def remove_econsent(self):
        self.mongo_database[DEPLOYMENT_COLLECTION].update_one(
            {"_id": ObjectId(self.deployment_id)},
            {"$unset": {"econsent": 1}},
        )
