from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34788d"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT = "600720843111683010a73b4e"
VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT = "6009d2409b0e1f2eab20bbb3"


class TagRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super().setUp()

        self.base_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/tags"

    def headers(self, role: str = "Admin", user_id: str = None):
        if not user_id:
            user_id = VALID_MANAGER_ID if role == "Admin" else VALID_USER_ID
        return self.get_headers_for_token(user_id)

    def test_success_create_tag_by_admin(self):
        tag = {"starred": "true"}
        rsp = self.flask_client.post(self.base_route, json=tag, headers=self.headers())
        user_id = rsp.json["id"]
        self.assertEqual(201, rsp.status_code)
        self.assertEqual(VALID_USER_ID, user_id)

        # check if tag log has been created
        result = self.mongo_database["taglog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_create_tag_by_contributor(self):
        tag = {"starred": "true"}
        rsp = self.flask_client.post(
            self.base_route,
            json=tag,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        user_id = rsp.json["id"]
        self.assertEqual(201, rsp.status_code)
        self.assertEqual(VALID_USER_ID, user_id)

        # check if tag log has been created
        result = self.mongo_database["taglog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_create_tag_by_custom_role_with_manage_patient_permission(self):
        tag = {
            "deploymentId": DEPLOYMENT_ID,
            "starred": "true",
        }

        rsp = self.flask_client.post(
            self.base_route,
            json=tag,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT
            ),
        )
        user_id = rsp.json["id"]
        self.assertEqual(201, rsp.status_code)
        self.assertEqual(VALID_USER_ID, user_id)

        # check if tag log has been created
        result = self.mongo_database["taglog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_failure_create_tag_by_custom_role_with_out_manage_patient_permission(self):
        tag = {"starred": "false"}
        rsp = self.flask_client.post(
            self.base_route,
            json=tag,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
            ),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_delete_tag_by_admin(self):
        rsp = self.flask_client.delete(self.base_route, headers=self.headers())
        self.assertEqual(204, rsp.status_code)

    def test_success_delete_tag_by_contributor(self):
        rsp = self.flask_client.delete(
            self.base_route,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(204, rsp.status_code)

    def test_success_delete_tag_by_custom_role_with_manage_patient_permission(self):
        rsp = self.flask_client.delete(
            self.base_route,
            query_string={"deploymentId": DEPLOYMENT_ID},
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT
            ),
        )
        self.assertEqual(204, rsp.status_code)

    def test_failure_delete_tag_by_custom_role_with_out_manage_patient_permission(self):
        rsp = self.flask_client.delete(
            self.base_route,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
            ),
        )
        self.assertEqual(403, rsp.status_code)
