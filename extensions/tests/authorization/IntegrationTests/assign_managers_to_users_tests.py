from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import Role
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.utils.validators import utc_str_val_to_field

VALID_USER_ID_1 = "5e8f0c74b50aa9656c34789b"
VALID_USER_ID_2 = "5e8f0c74b50aa9656c34789c"
VALID_USER_ID_3 = "61fb852583e256e58e7ea9e3"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"
VALID_MANAGER_ID_1 = "5e8f0c74b50aa9656c34789d"
VALID_MANAGER_ID_2 = "5e8f0c74b50aa9656c34788d"
VALID_SUPER_ADMIN_ID = "602ce48712b129679a501570"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
CUSTOM_ROLE_1_ID_DEPLOYMENT_X = "600720843111683010a73b4e"
CUSTOM_ROLE_2_ID_DEPLOYMENT_X = "6009d2409b0e1f2eab20bbb3"

MANAGER_WITH_NO_USERS = "449213d10b6d06b35e133e79"
VALID_MANAGER_1_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
INVALID_MANAGER_ID = "5e8f0c74b50aa9656c34786c"
DEPLOYMENT_ID_1 = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_ID_2 = "5ed8ae76cf99540b259a7315"


class BaseAssignManagersToUsersTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/assign_managers_dump.json"),
    ]
    override_config = {"server.authorization.enableAuthz": "true"}

    def setUp(self):
        super().setUp()
        self.user_path = "/api/extensions/v1beta/user"
        self.assign_path = f"{self.user_path}/assign"
        self.headers = self.get_headers_for_token(VALID_MANAGER_ID_1)


class AssignManagersToUsersTestCase(BaseAssignManagersToUsersTestCase):
    USER_IDS_FIELD = "userIds"
    MANAGER_IDS_FIELD = "managerIds"
    ALL_USERS_FIELDS = "allUsers"

    def assertRecordsUpdated(self, old_record: dict, new_record: dict):
        previous_update_datetime = utc_str_val_to_field(old_record["updateDateTime"])
        new_update_datetime = utc_str_val_to_field(new_record["updateDateTime"])
        self.assertGreater(new_update_datetime, previous_update_datetime)

    def get_user_collection(self):
        return self.mongo_database["user"]

    def get_assignment_collection(self):
        return self.mongo_database["patientmanagerassignment"]

    def get_assignment_log_collection(self):
        return self.mongo_database["patientmanagerassignmentlog"]

    def get_existing_assignment_record(self, user_id: str):
        collection = self.get_assignment_collection()
        return collection.find_one({"_id": ObjectId(user_id)})

    def get_user_ids_in_deployment(self, deployment_id: str):
        collection = self.get_user_collection()
        users = collection.find(
            {"roles.resource": f"deployment/{deployment_id}", "roles.roleId": "User"}
        )
        return [str(user.get("_id")) for user in users]

    def post(self, url, json, headers):
        return self.flask_client.post(url, json=json, headers=headers)

    def post_with_manager_headers(self, url, json):
        return self.post(url, json, self.headers)

    def test_success_assign_admin_to_new_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        self.post_with_manager_headers(self.assign_path, body)

        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNotNone(new_record)

    def test_success_assign_invalid_admin_to_user(self):
        body = {
            self.MANAGER_IDS_FIELD: ["449213d10b6d06b35e133b79"],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        r = self.post_with_manager_headers(self.assign_path, body)
        self.assertEqual(403, r.status_code)
        self.assertEqual(100050, r.json["code"])

    def test_success_assign_admin_to_old_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(VALID_MANAGER_ID_1, str(old_record[self.MANAGER_IDS_FIELD][0]))

        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post_with_manager_headers(self.assign_path, body)

        new_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(VALID_MANAGER_ID_1, str(new_record[self.MANAGER_IDS_FIELD][0]))

        self.assertRecordsUpdated(old_record, new_record)

    def test_success_assign_contributor_to_new_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [CONTRIBUTOR_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )

        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNotNone(new_record)

    def test_success_assign_contributor_to_old_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(VALID_MANAGER_ID_1, str(old_record[self.MANAGER_IDS_FIELD][0]))

        body = {
            self.MANAGER_IDS_FIELD: [CONTRIBUTOR_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )

        new_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(
            CONTRIBUTOR_1_ID_DEPLOYMENT_X, str(new_record[self.MANAGER_IDS_FIELD][0])
        )

        self.assertRecordsUpdated(old_record, new_record)

    def test_success_assign_managers_to_multiple_users(self):
        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_1, VALID_USER_ID_2],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(VALID_MANAGER_ID_1),
        )
        for user_id in body[self.USER_IDS_FIELD]:
            assignment_record = self.get_existing_assignment_record(user_id)
            for manager_id in body[self.MANAGER_IDS_FIELD]:
                self.assertIn(
                    ObjectId(manager_id),
                    assignment_record[self.MANAGER_IDS_FIELD],
                )

    def test_success_assign_managers_to_all_users(self):
        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [],
            self.ALL_USERS_FIELDS: True,
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(VALID_MANAGER_ID_1),
        )
        all_user_ids_in_deployment = self.get_user_ids_in_deployment(
            VALID_MANAGER_1_DEPLOYMENT_ID
        )

        for user_id in all_user_ids_in_deployment:
            assignment_record = self.get_existing_assignment_record(user_id)
            self.assertEqual(
                VALID_MANAGER_ID_1,
                str(assignment_record[self.MANAGER_IDS_FIELD][0]),
            )

    def test_success_assign_custom_role_with_manage_patient_data_to_new_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )

        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNotNone(new_record)

    def test_success_assign_custom_role_with_manage_patient_data_to_old_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(VALID_MANAGER_ID_1, str(old_record[self.MANAGER_IDS_FIELD][0]))

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )

        new_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(
            CUSTOM_ROLE_1_ID_DEPLOYMENT_X, str(new_record[self.MANAGER_IDS_FIELD][0])
        )

        self.assertRecordsUpdated(old_record, new_record)

    def test_failure_assign_custom_role_with_out_manage_patient_data_to_new_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_2_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        rsp = self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_assign_custom_role_with_out_manage_patient_data_to_old_user(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(VALID_MANAGER_ID_1, str(old_record[self.MANAGER_IDS_FIELD][0]))

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_2_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        rsp = self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_user_assign_admin(self):
        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        response = self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(VALID_USER_ID_1),
        )
        self.assertEqual(403, response.status_code)

    def test_success_log_created(self):
        log_collection = self.get_assignment_log_collection()
        records_count = log_collection.count()
        self.assertEqual(0, records_count)

        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post_with_manager_headers(self.assign_path, body)

        records_count = log_collection.count()
        self.assertEqual(1, records_count)

    def test_success_log_created_by_contributor(self):
        log_collection = self.get_assignment_log_collection()
        records_count = log_collection.count()
        self.assertEqual(0, records_count)

        body = {
            self.MANAGER_IDS_FIELD: [CONTRIBUTOR_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )

        records_count = log_collection.count()
        self.assertEqual(1, records_count)

    def test_success_log_created_by_custom_role_with_manage_patient_data(self):
        log_collection = self.get_assignment_log_collection()
        records_count = log_collection.count()
        self.assertEqual(0, records_count)

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_1_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )

        records_count = log_collection.count()
        self.assertEqual(1, records_count)

    def test_failure_log_created_by_custom_role_with_out_manage_patient_data(self):
        log_collection = self.get_assignment_log_collection()
        records_count = log_collection.count()
        self.assertEqual(0, records_count)

        body = {
            self.MANAGER_IDS_FIELD: [CUSTOM_ROLE_2_ID_DEPLOYMENT_X],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        rsp = self.post(
            self.assign_path,
            body,
            self.get_headers_for_token(CUSTOM_ROLE_2_ID_DEPLOYMENT_X),
        )

        self.assertEqual(403, rsp.status_code)

    def test_success_clear_assignment(self):
        body = {
            self.MANAGER_IDS_FIELD: [],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        self.post_with_manager_headers(self.assign_path, body)

        new_record = self.get_existing_assignment_record(VALID_USER_ID_2)
        self.assertEqual(0, len(new_record[self.MANAGER_IDS_FIELD]))

    def test_failure_assign_user_to_user(self):
        body = {
            self.MANAGER_IDS_FIELD: [VALID_USER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_2],
        }
        assign_path = self.assign_path
        response = self.post(assign_path, body, self.headers)
        self.assertEqual(403, response.status_code)


class RetrieveAssignedManagersTestCase(BaseAssignManagersToUsersTestCase):
    ASSIGNED_MANAGERS_FIELD_NAME = "assignedManagers"
    ASSIGNED_USERS_COUNT_FIELD_NAME = "assignedUsersCount"

    def get_user_profile(self, user_id: str, manager_id: str = None):
        response = self.flask_client.get(
            f"{self.user_path}/{user_id}",
            query_string={"deploymentId": DEPLOYMENT_ID_1},
            headers=self.get_headers_for_token(
                manager_id if manager_id else VALID_MANAGER_ID_1
            ),
        )
        if not manager_id:
            self.assertEqual(200, response.status_code)
        return response.json

    def test_success_retrieve_assigned_managers(self):
        response_json = self.get_user_profile(VALID_USER_ID_2)
        field_name = self.ASSIGNED_MANAGERS_FIELD_NAME
        self.assertIn(field_name, response_json)
        self.assertEqual(VALID_MANAGER_ID_1, response_json[field_name][0])

    def test_success_retrieve_assigned_managers_by_contributor(self):
        response_json = self.get_user_profile(
            VALID_USER_ID_2, CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        field_name = self.ASSIGNED_MANAGERS_FIELD_NAME
        self.assertIn(field_name, response_json)
        self.assertEqual(VALID_MANAGER_ID_1, response_json[field_name][0])

    def test_success_retrieve_assigned_managers_by_custom_role(self):
        response_json = self.get_user_profile(
            VALID_USER_ID_2, CUSTOM_ROLE_1_ID_DEPLOYMENT_X
        )
        field_name = self.ASSIGNED_MANAGERS_FIELD_NAME
        self.assertIn(field_name, response_json)
        self.assertEqual(VALID_MANAGER_ID_1, response_json[field_name][0])

    def test_success_retrieve_empty_list_for_user_with_no_assigned_managers(self):
        response_json = self.get_user_profile(VALID_USER_ID_3)
        field_name = self.ASSIGNED_MANAGERS_FIELD_NAME
        self.assertIn(field_name, response_json)
        self.assertEqual(0, len(response_json[field_name]))

    def test_retrieve_manager_with_no_assigned_users(self):
        headers = self.get_headers_for_token(MANAGER_WITH_NO_USERS)
        response = self.flask_client.get(
            f"{self.user_path}/profiles/assigned", headers=headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.json), 0)

    def test_success_retrieve_users_with_assigned_managers(self):
        response = self.flask_client.post(
            f"{self.user_path}/profiles", json={}, headers=self.headers
        )
        self.assertEqual(200, response.status_code)

        field_name = self.ASSIGNED_MANAGERS_FIELD_NAME
        for user in response.json:
            self.assertIn(field_name, user)
            if user["id"] in [VALID_USER_ID_1, VALID_USER_ID_2]:
                self.assertEqual(3, len(user[field_name]))
            else:
                self.assertEqual(0, len(user[field_name]))

    def _get_profiles_by_second_manager(self, body: dict):
        headers = self.get_headers_for_token(VALID_MANAGER_ID_2)
        return self.flask_client.post(
            f"{self.user_path}/profiles", json=body, headers=headers
        )

    def test_failure_retrieve_managers_negative_skip_value(self):
        body = {
            RetrieveProfilesRequestObject.ROLE: Role.UserType.MANAGER,
            RetrieveProfilesRequestObject.SKIP: -1,
        }
        response = self._get_profiles_by_second_manager(body)
        self.assertEqual(403, response.status_code)

    def test_failure_retrieve_managers_negative_limit_value(self):
        body = {
            RetrieveProfilesRequestObject.ROLE: Role.UserType.MANAGER,
            RetrieveProfilesRequestObject.LIMIT: -1,
        }
        response = self._get_profiles_by_second_manager(body)
        self.assertEqual(403, response.status_code)

    def test_success_retrieve_managers_with_assigned_patients_count(self):
        body = {RetrieveProfilesRequestObject.ROLE: Role.UserType.MANAGER}
        response = self._get_profiles_by_second_manager(body)
        self.assertEqual(200, response.status_code)

        field_name = self.ASSIGNED_USERS_COUNT_FIELD_NAME
        filtered = filter(lambda user: user["id"] == VALID_MANAGER_ID_1, response.json)
        manager = next(filtered, None)
        self.assertIsNotNone(manager)
        self.assertIn(field_name, manager)
        self.assertEqual(4, manager[field_name])

    def test_success_retrieve_assigned_users(self):
        response = self.flask_client.get(
            f"{self.user_path}/profiles/assigned", headers=self.headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))

    def test_success_retrieve_assigned_users_for_another_manager_same_deployment(self):
        manager_id = VALID_MANAGER_ID_2
        response = self.flask_client.get(
            f"{self.user_path}/{manager_id}/profiles/assigned", headers=self.headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json))

    def test_failure_retrieve_assigned_users_for_another_manager_another_deployment(
        self,
    ):
        manager_id = INVALID_MANAGER_ID
        response = self.flask_client.get(
            f"{self.user_path}/{manager_id}/profiles/assigned",
            query_string={"deploymentId": DEPLOYMENT_ID_2},
            headers=self.headers,
        )
        self.assertEqual(403, response.status_code)
        self.assertEqual(100004, response.json["code"])

    def test_failure_retrieve_assigned_users_for_invalid_manager(
        self,
    ):
        response = self.flask_client.get(
            f"{self.user_path}/{INVALID_MANAGER_ID}/profiles/assigned",
            headers=self.headers,
        )
        self.assertEqual(404, response.status_code)

    def test_failure_retrieve_assigned_users_by_user(self):
        response = self.flask_client.get(
            f"{self.user_path}/profiles/assigned",
            headers=self.get_headers_for_token(VALID_USER_ID_1),
        )
        self.assertEqual(403, response.status_code)


class DeleteUserManagerTest(BaseAssignManagersToUsersTestCase):
    MANAGER_IDS_FIELD = "managerIds"
    USER_IDS_FIELD = "userIds"

    def get_assignment_collection(self):
        return self.mongo_database["patientmanagerassignment"]

    def get_assignment_log_collection(self):
        return self.mongo_database["patientmanagerassignmentlog"]

    def get_existing_assignment_record(self, user_id: str):
        collection = self.get_assignment_collection()
        return collection.find_one({"_id": ObjectId(user_id)})

    def post(self, url, json):
        response = self.flask_client.post(url, json=json, headers=self.headers)
        self.assertEqual(201, response.status_code)
        return response

    def test_success_delete_user_is_patient(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        self.post(self.assign_path, body)
        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNotNone(new_record)

        super_admin_headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        del_user_path = f"/api/extensions/v1beta/user/{VALID_USER_ID_1}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=super_admin_headers)
        self.assertEqual(rsp.status_code, 204)

        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(new_record)

    def test_success_delete_user_is_manager(self):
        old_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNone(old_record)

        body = {
            self.MANAGER_IDS_FIELD: [VALID_MANAGER_ID_2, VALID_MANAGER_ID_1],
            self.USER_IDS_FIELD: [VALID_USER_ID_1],
        }
        self.post(self.assign_path, body)
        new_record = self.get_existing_assignment_record(VALID_USER_ID_1)
        self.assertIsNotNone(new_record)

        super_admin_headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        del_user_path = f"/api/extensions/v1beta/user/{VALID_MANAGER_ID_2}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=super_admin_headers)
        self.assertEqual(rsp.status_code, 204)

        res = self.get_existing_assignment_record(VALID_USER_ID_1)
        managers_in_res = [str(i) for i in res["managerIds"]]
        self.assertNotIn(VALID_MANAGER_ID_2, managers_in_res)
