from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.router.user_profile_request import (
    RetrieveStaffRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.utils.common_functions_utils import find

ORGANIZATION_ID = "5fde855f12db509a2785da06"
ORG_STAFF_ID = "5ed803dd5f2f99da73654413"


class StaffListTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/organization_dump.json"),
        Path(__file__).parent.joinpath("fixtures/assign_managers_dump.json"),
    ]
    base_path = "/api/extensions/v1beta/user/staff"

    def setUp(self):
        super(StaffListTests, self).setUp()
        self.headers = self.get_headers_for_token(ORG_STAFF_ID)

    def test_success_retrieve_staff_list(self):
        body = {RetrieveStaffRequestObject.ORGANIZATION_ID: ORGANIZATION_ID}
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        staff_list = rsp.json
        self.assertTrue(isinstance(staff_list, list))
        self.assertGreater(len(staff_list), 0)
        ref_member = find(lambda x: x["email"] == "organization@staff.com", staff_list)
        self.assertEqual(1, ref_member.get("assignedUsersCount"))

    def test_success_retrieve_staff_list_no_deployments_in_organization(self):
        result = self.mongo_database.organization.update_one(
            {
                "_id": ObjectId(ORGANIZATION_ID),
            },
            {"$unset": {"deploymentIds": ""}},
        )
        self.assertEqual(1, result.modified_count)
        body = {RetrieveStaffRequestObject.ORGANIZATION_ID: ORGANIZATION_ID}
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

    def test_failure_retrieve_staff_list_no_permission_in_organization(self):
        org_id = "6156ad33a7082b29f6c6d0e8"
        body = {RetrieveStaffRequestObject.ORGANIZATION_ID: org_id}
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_staff_list_contains_super_admin_name(self):
        # that was causing 500 error as there are a lot of test super admin
        # user that were using SuperAdmin as a name
        body = {
            RetrieveStaffRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            RetrieveStaffRequestObject.NAME_CONTAINS: "SuperAdmin",
        }
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json))

    def test_success_retrieve_staff_list_search(self):
        body = {
            RetrieveStaffRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            RetrieveStaffRequestObject.NAME_CONTAINS: "organizat",  # user name is `Organization Staff`
        }
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertGreater(len(rsp.json), 0)

    def test_success_retrieve_staff_list_search_no_results(self):
        body = {
            RetrieveStaffRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            RetrieveStaffRequestObject.NAME_CONTAINS: "das",
        }
        rsp = self.flask_client.post(self.base_path, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json))

    def test_failure_retrieve_staff_no_body(self):
        rsp = self.flask_client.post(self.base_path, headers=self.headers)
        self.assertEqual(400, rsp.status_code)
