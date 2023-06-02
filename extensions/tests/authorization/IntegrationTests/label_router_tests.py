from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.router.user_profile_request import (
    AssignLabelsToUsersRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
VALID_USER_ID2 = "61fb852583e256e58e7ea9e1"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34788d"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
LABEL_ID_1 = "5e8eeae1b707216625ca4202"
LABEL_ID_2 = "5d386cc6ff885918d96edb2c"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT = "600720843111683010a73b4e"
VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT = "6009d2409b0e1f2eab20bbb3"


class LabelRouterTestCase(ExtensionTestCase):
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

        self.single_user_base_route = (
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/labels"
        )
        self.bulk_user_base_route = f"/api/extensions/v1beta/user/labels"

    def headers(self, role: str = "Admin", user_id: str = None):
        if not user_id:
            user_id = VALID_MANAGER_ID if role == "Admin" else VALID_USER_ID
        return self.get_headers_for_token(user_id)

    def test_success_assign_label_by_admin(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route, json=label, headers=self.headers()
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["id"]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_assign_no_label_to_a_user(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route, json=label, headers=self.headers()
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["id"]
        self.assertEqual(VALID_USER_ID, user_id)

    def test_success_assign_labels_to_user_by_admin(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1, LABEL_ID_2],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route, json=label, headers=self.headers()
        )

        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["id"]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_failure_assign_labels_to_no_user_by_admin(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1, LABEL_ID_2],
            AssignLabelsToUsersRequestObject.USER_IDS: [],
        }
        rsp = self.flask_client.post(
            self.bulk_user_base_route, json=label, headers=self.headers()
        )

        self.assertEqual(403, rsp.status_code)

    def test_failure_no_label_to_users_by_admin(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [],
            AssignLabelsToUsersRequestObject.USER_IDS: [VALID_USER_ID, VALID_USER_ID2],
        }
        rsp = self.flask_client.post(
            self.bulk_user_base_route, json=label, headers=self.headers()
        )

        self.assertEqual(403, rsp.status_code)

    def test_success_assign_labels_to_multi_user_by_admin(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1, LABEL_ID_2],
            AssignLabelsToUsersRequestObject.USER_IDS: [VALID_USER_ID, VALID_USER_ID2],
        }
        rsp = self.flask_client.post(
            self.bulk_user_base_route, json=label, headers=self.headers()
        )
        self.assertEqual(200, rsp.status_code)

        user_id = rsp.json[0]
        self.assertEqual(len(rsp.json), 2)
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_assign_label_by_contributor(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route,
            json=label,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["id"]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_assign_bulk_label_by_contributor(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
            AssignLabelsToUsersRequestObject.USER_IDS: [VALID_USER_ID, VALID_USER_ID2],
        }
        rsp = self.flask_client.post(
            self.bulk_user_base_route,
            json=label,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json[0]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_assign_label_by_custom_role_with_manage_patient_permission(self):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
        }

        rsp = self.flask_client.post(
            self.single_user_base_route,
            json=label,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT
            ),
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json["id"]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_success_bulk_assign_label_by_custom_role_with_manage_patient_permission(
        self,
    ):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
            AssignLabelsToUsersRequestObject.USER_IDS: [VALID_USER_ID, VALID_USER_ID2],
        }

        rsp = self.flask_client.post(
            self.bulk_user_base_route,
            json=label,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT
            ),
        )
        self.assertEqual(200, rsp.status_code)
        user_id = rsp.json[0]
        self.assertEqual(VALID_USER_ID, user_id)

        # check if label log has been created
        result = self.mongo_database["labellog"].find_one({"userId": ObjectId(user_id)})
        self.assertIsNotNone(result)

    def test_failure_assign_label_by_custom_role_with_out_manage_patient_permission(
        self,
    ):
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [LABEL_ID_1],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route,
            json=label,
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
            ),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_assign_label_with_invalid_label_id(self):
        INVALID_LABEL_ID = "5e8f0c74b50aa9656c34788d"
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [INVALID_LABEL_ID],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route,
            json=label,
            headers=self.headers(),
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_bulk_assign_label_with_invalid_label_id(self):
        INVALID_LABEL_ID = "5e8f0c74b50aa9656c34788d"
        label = {
            AssignLabelsToUsersRequestObject.LABEL_IDS: [INVALID_LABEL_ID],
            AssignLabelsToUsersRequestObject.USER_IDS: [VALID_USER_ID, VALID_USER_ID2],
        }
        rsp = self.flask_client.post(
            self.single_user_base_route,
            json=label,
            headers=self.headers(),
        )
        self.assertEqual(404, rsp.status_code)
