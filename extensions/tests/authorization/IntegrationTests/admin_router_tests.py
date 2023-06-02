from bson import ObjectId

from extensions.authorization.middleware import AuthorizationMiddleware
from extensions.authorization.models.role.role import RoleName, Role
from extensions.authorization.models.user import RoleAssignment
from extensions.common.s3object import S3Object
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.learn import (
    Learn,
    LearnSection,
    LearnArticle,
    LearnArticleContent,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.tests.authorization.IntegrationTests.abstract_permission_test_case import (
    AbstractPermissionTestCase,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_consent,
    get_learn_section,
    get_article,
    get_deployment,
)
from extensions.tests.shared.test_helpers import get_module_config

SUPER_ADMIN_ID = "5ed803dd5f2f99da73684413"
HUMA_SUPPORT_ID = "5ed803dd5f2f99da73675513"
ORGANIZATION_OWNER_ID = "61cb194c630781b664bc7eb5"
USER_ID = "5e8f0c74b50aa9656c34789b"
MANAGER_ID = "5e8f0c74b50aa9656c34789d"
ORGANIZATION_EDITOR_ID = "5ed803dd5f2f99da73675555"
ACCOUNT_MANAGER_ID = "5e84b0dab8dfa268b1180336"

ORGANIZATION_ID = "5fde855f12db509a2785da06"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
NO_ORG_DEPLOYMENT_ID = "5d386cc6ff885918d96eaaaa"
LEARN_SECTION_ID = "5e946c69e8002eac4a107f56"


class DeploymentCRUDPermissionTestCase(AbstractPermissionTestCase):
    """
    - two deployments: X, Y
    - two users / manager for deployment X: user1, user2, manager1, manager2
    - one users / manager for deployment Y: user3, manager3
    - admin can create deployment or admin_data
    - user or manager can't create deployment or admin_data
    """

    def setUp(self):
        super().setUp()
        self.base_path = "/api/extensions/v1beta/deployment"
        self.admin_headers = self.get_headers_for_token(SUPER_ADMIN_ID)
        self.support_headers = self.get_headers_for_token(HUMA_SUPPORT_ID)
        self.owner_headers = self.get_headers_for_token(ORGANIZATION_OWNER_ID)
        self.manager_headers = self.get_headers_for_token(MANAGER_ID)
        self.user_headers = self.get_headers_for_token(USER_ID)
        self.org_editor_headers = self.get_headers_for_token(ORGANIZATION_EDITOR_ID)

    def test_successful_create_deployment_by_super_admin(self):
        rsp = self.flask_client.post(
            self.base_path, json=get_deployment("TEST_X"), headers=self.admin_headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

    def test_successful_create_deployment_by_huma_support(self):
        rsp = self.flask_client.post(
            self.base_path, json=get_deployment("TEST_X"), headers=self.support_headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

    def test_successful_create_deployment_by_org_owner(self):
        rsp = self.flask_client.post(
            self.base_path, json=get_deployment("TEST_X"), headers=self.owner_headers
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

    def test_failure_create_deployment_by_user(self):
        rsp = self.flask_client.post(
            self.base_path, json=get_deployment("TEST_X"), headers=self.user_headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_deployment_by_manager(self):
        rsp = self.flask_client.post(
            self.base_path, json=get_deployment("TEST_X"), headers=self.manager_headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_successful_create_module_configs(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/module-config",
            json=get_module_config(),
            headers=self.admin_headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_module_configs_by_user(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/module-config",
            json=get_module_config(),
            headers=self.user_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_module_configs_by_manager(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/module-config",
            json=get_module_config(),
            headers=self.manager_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_successful_create_consent(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/consent",
            json=get_consent(),
            headers=self.admin_headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_successful_create_consent_by_huma_support(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/consent",
            json=get_consent(),
            headers=self.support_headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_consent_by_user(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/consent",
            json=get_consent(),
            headers=self.user_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_consent_by_manager(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/{DEPLOYMENT_ID}/consent",
            json=get_consent(),
            headers=self.manager_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_successful_create_learn_section(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section",
            json=get_learn_section(),
            headers=self.admin_headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_learn_section_by_user(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section",
            json=get_learn_section(),
            headers=self.user_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_learn_section_by_manager(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section",
            json=get_learn_section(),
            headers=self.manager_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_successful_create_learn_article(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section/{LEARN_SECTION_ID}/article",
            json=get_article(),
            headers=self.admin_headers,
        )
        self.assertEqual(201, rsp.status_code)

        collection_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        deployment_data = self.mongo_database[collection_name].find_one(
            {Deployment.ID_: ObjectId(DEPLOYMENT_ID)}
        )
        article_data = deployment_data[Deployment.LEARN][Learn.SECTIONS][0][
            LearnSection.ARTICLES
        ][1]
        expected_res = {
            S3Object.BUCKET: "integrationtests",
            S3Object.KEY: "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
            S3Object.REGION: "cn",
        }
        self.assertEqual(
            expected_res,
            article_data[LearnArticle.CONTENT][LearnArticleContent.CONTENT_OBJECT],
        )

    def test_successful_create_learn_article_by_huma_support(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section/{LEARN_SECTION_ID}/article",
            json=get_article(),
            headers=self.support_headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_failure_create_learn_article_by_user(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section/{LEARN_SECTION_ID}/article",
            json=get_article(),
            headers=self.user_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_create_learn_article_by_manager(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/{DEPLOYMENT_ID}/learn-section/{LEARN_SECTION_ID}/article",
            json=get_article(),
            headers=self.manager_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_deployment_org_owner(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{DEPLOYMENT_ID}", headers=self.owner_headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_retrieve_deployment_org_owner_no_permission(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{NO_ORG_DEPLOYMENT_ID}", headers=self.owner_headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_update_deployment_org_owner(self):
        rsp = self.flask_client.put(
            f"{self.base_path}/{DEPLOYMENT_ID}",
            json={"name": "Updated"},
            headers=self.owner_headers,
        )
        self.assertEqual(200, rsp.status_code)
        updated_count = self.mongo_database.deployment.count_documents(
            {"name": "Updated"}
        )
        self.assertEqual(1, updated_count)

    def test_failure_update_deployment_org_owner_no_permission(self):
        rsp = self.flask_client.put(
            f"{self.base_path}/{NO_ORG_DEPLOYMENT_ID}",
            json={"name": "Updated"},
            headers=self.owner_headers,
        )
        self.assertEqual(403, rsp.status_code)
        updated_count = self.mongo_database.deployment.count_documents(
            {"name": "Updated"}
        )
        self.assertEqual(0, updated_count)

    def test_success_retrieve_deployment_org_editor(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{DEPLOYMENT_ID}", headers=self.org_editor_headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_create_deployment_org_editor(self):
        rsp = self.flask_client.post(
            self.base_path,
            json=get_deployment("TEST_X"),
            headers=self.org_editor_headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_search_all_deployment_access_controller_with_org_owner(self):
        self._add_org_owner(ACCOUNT_MANAGER_ID, ORGANIZATION_ID)
        headers = self.get_headers_for_token(ACCOUNT_MANAGER_ID)
        headers["x-org-id"] = ORGANIZATION_ID
        rsp = self.flask_client.post(
            f"{self.base_path}/search", json={"skip": 0, "limit": 100}, headers=headers
        )
        self.assertEqual(403, rsp.status_code)

    def _add_org_owner(self, user_id: str, organization_id: str):
        role = {
            RoleAssignment.ROLE_ID: RoleName.ORGANIZATION_OWNER,
            RoleAssignment.RESOURCE: f"organization/{organization_id}",
            RoleAssignment.USER_TYPE: Role.UserType.SUPER_ADMIN,
        }
        self.mongo_database.user.update(
            {"_id": ObjectId(user_id)},
            {"$push": {"roles": role}},
        )


class OrganizationCRUDPermissionTestCase(AbstractPermissionTestCase):
    def setUp(self):
        super().setUp()
        self.ac_headers = self.get_headers_for_token(ACCOUNT_MANAGER_ID)
        self.org_route = "/api/extensions/v1beta/organization"

    def test_failure_search_all_organizations(self):
        self._add_org_owner(ACCOUNT_MANAGER_ID, ORGANIZATION_ID)
        headers = {
            **self.ac_headers,
            AuthorizationMiddleware.ORGANIZATION_HEADER_KEY: ORGANIZATION_ID,
        }
        rsp = self.flask_client.post(
            f"{self.org_route}/search", headers=headers, json={"skip": 0, "limit": 100}
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual("Action not allowed for current user.", rsp.json["message"])

    def _add_org_owner(self, user_id: str, organization_id: str):
        role = {
            RoleAssignment.ROLE_ID: RoleName.ORGANIZATION_OWNER,
            RoleAssignment.RESOURCE: f"organization/{organization_id}",
            RoleAssignment.USER_TYPE: Role.UserType.SUPER_ADMIN,
        }
        self.mongo_database.user.update(
            {"_id": ObjectId(user_id)},
            {"$push": {"roles": role}},
        )
