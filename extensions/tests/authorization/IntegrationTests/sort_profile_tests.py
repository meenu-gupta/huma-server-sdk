from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.router.user_profile_response import (
    RetrieveProfilesResponseObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789d"

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
PROFILES_USER_ID_1 = VALID_USER_ID
PROFILES_USER_ID_2 = "5e8f0c74b50aa9656c34789c"
OFF_BOARDED_USERS_ID = "5e8f0c74b50aa9656c34789e"
RED_GRAY_RAG_NO_FLAGS_USER_ID = "61fb852583e256e58e7ea9e3"
RED_AMBER_GRAY_RAG_NO_FLAGS_USER_ID = "61fb852583e256e58e7ea9e4"


class SortProfilesTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        StorageComponent(),
        OrganizationComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    config_file_path = Path(__file__).with_name("config.test.yaml")
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/sort_deployment_dump.json"),
        Path(__file__).parent.joinpath("fixtures/organization_dump.json"),
        Path(__file__).parent.joinpath("fixtures/unseenrecentresult.json"),
    ]

    def setUp(self):
        super().setUp()

        self._config = self.config_class.get(
            self.config_file_path, self.override_config
        )
        self.headers = self.get_headers_for_token(VALID_MANAGER_ID)
        self.base_route = "/api/extensions/v1/user/profiles"

    def test_success_retrieve_profiles(self):
        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            5, len(rsp.json[RetrieveProfilesResponseObject.Response.USERS])
        )

    def test_success_retrieve_profiles_with_pagination(self):
        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertIn(RetrieveProfilesResponseObject.Response.TOTAL, rsp.json)
        self.assertIn(RetrieveProfilesResponseObject.Response.FILTERED, rsp.json)
        self.assertEqual(5, rsp.json[RetrieveProfilesResponseObject.Response.FILTERED])
        self.assertEqual(
            5, len(rsp.json[RetrieveProfilesResponseObject.Response.USERS])
        )

    def test_success_sort_flags_and_rag_descending(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        body = {"sort": {"fields": ["FLAGS"], "order": "DESCENDING"}}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        users_key = RetrieveProfilesResponseObject.Response.USERS
        self.assertEqual(5, len(rsp.json[users_key]))

        # users without flags will be sort based on their RAG
        self.assertEqual(
            RED_AMBER_GRAY_RAG_NO_FLAGS_USER_ID, rsp.json[users_key][2]["id"]
        )
        self.assertEqual(RED_GRAY_RAG_NO_FLAGS_USER_ID, rsp.json[users_key][3]["id"])

        # off boarded users are always at the end
        self.assertEqual(OFF_BOARDED_USERS_ID, rsp.json[users_key][-1]["id"])

    def test_success_sort_flags_and_rag_ascending(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        body = {"sort": {"fields": ["FLAGS"], "order": "ASCENDING"}}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        users_key = RetrieveProfilesResponseObject.Response.USERS
        self.assertEqual(5, len(rsp.json[users_key]))

        # users without flags will be sort based on their RAG
        self.assertEqual(
            RED_AMBER_GRAY_RAG_NO_FLAGS_USER_ID, rsp.json[users_key][1]["id"]
        )
        self.assertEqual(RED_GRAY_RAG_NO_FLAGS_USER_ID, rsp.json[users_key][0]["id"])

        # off boarded users are always at the end
        self.assertEqual(OFF_BOARDED_USERS_ID, rsp.json[users_key][-1]["id"])
