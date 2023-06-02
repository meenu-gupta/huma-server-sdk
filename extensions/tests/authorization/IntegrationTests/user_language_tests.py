from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.abstract_permission_test_case import (
    AbstractPermissionTestCase,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    USER_1_ID_DEPLOYMENT_X,
)
from sdk.auth.component import AuthComponent
from sdk.versioning.component import VersionComponent


class UserLanguageTestCase(AbstractPermissionTestCase):
    SERVER_VERSION = "1.3.1"
    API_VERSION = "v1"
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        VersionComponent(server_version=SERVER_VERSION, api_version=API_VERSION),
    ]

    def setUp(self):
        super().setUp()
        self.base_path = "/api/extensions/v1beta/user"

    def test_success_update_user_language_with_configuration_api(self):
        headers = self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X)
        headers["x-hu-locale"] = "ar"
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=headers,
        )
        self.assertEqual("ar", rsp.json[User.LANGUAGE])

    def test_success_get_user_configuration_with_invalid_lang(self):
        headers = self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X)
        headers["x-hu-locale"] = "invalid-lang"
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=headers,
        )
        self.assertEqual("en", rsp.json[User.LANGUAGE])
