from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes

NOT_VERIFIED_USER_ID = "6034bfa242276aaded6ad685"


class OnboardUserTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        KeyActionComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/users_dump.json"),
    ]
    override_config = {"server.deployment.onBoarding": "true"}
    user_path = "/api/extensions/v1beta/user"

    @classmethod
    def setUpClass(cls) -> None:
        super(OnboardUserTests, cls).setUpClass()
        cls.headers = cls.get_headers_for_token(NOT_VERIFIED_USER_ID)

    def test_failure_user_verification_in_progress(self):
        rsp = self.flask_client.get(
            f"{self.user_path}/{NOT_VERIFIED_USER_ID}/key-action", headers=self.headers
        )
        self.assertEqual(428, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.ID_VERIFICATION_IN_PROGRESS)

    def test_success_call_user_profile_endpoint(self):
        rsp = self.flask_client.get(
            f"{self.user_path}/{NOT_VERIFIED_USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
