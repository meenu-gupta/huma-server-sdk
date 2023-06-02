from datetime import datetime
from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.middleware import AuthorizationMiddleware
from extensions.authorization.models.role.default_permissions import PermissionType
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import RoleAssignment
from extensions.common.sort import SortField
from extensions.dashboard.models.dashboard import DashboardId
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.status import Status
from extensions.exceptions import OrganizationErrorCodes
from extensions.organization.component import OrganizationComponent
from extensions.organization.models.organization import (
    Organization,
    OrganizationWithDeploymentInfo,
    DeploymentInfo,
)
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from extensions.organization.router.organization_requests import (
    RetrieveOrganizationsRequestObject,
    LinkDeploymentsRequestObject,
    UnlinkDeploymentsRequestObject,
)
from extensions.tests.deployment.UnitTests.test_helpers import (
    legal_docs_s3_fields,
    sample_s3_object,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes

VALID_SUPER_ADMIN_ID = "5e8f0c74b50aa9656c34789c"
VALID_USER_ID_WITHOUT_MANAGE_ORGANIZATION = "5e84b0dab8dfa268b1180536"
VALID_ACCOUNT_MANAGER_ID = "5e84b0dab8dfa268b1180336"
VALID_USER_WITH_MULTIPLE_ROLES = "61ddb98052da30cca00d5829"

VALID_ORGANIZATION_ID = "5fde855f12db509a2785da06"
INVALID_ORGANIZATION_ID = "5e84b0dab8dfa268b1180536"

VALID_DEPLOYMENT_ID = "5eff2fd31afbc05f76099f06"
INVALID_DEPLOYMENT_ID = "5ebb2fd31afbc05f76068eb6"

EXISTING_DEPLOYMENT_X = "5fde855f12db509a2785d899"
DEPLOYMENT_Y = "5fde8bbf12db509a2785dbb6"
DEPLOYMENT_Z = "61b4b195ff99e4b450077995"

CUSTOM_NEW_ROLE = "Custom New Role"
TEST_URL = "test.com"


def simple_organization():
    return {
        Organization.NAME: "ABC Pharmaceuticals EU Trials 1234",
        Organization.ENROLLMENT_TARGET: 3000,
        Organization.STUDY_COMPLETION_TARGET: 2800,
        Organization.STATUS: Status.DEPLOYED.value,
        Organization.PRIVACY_POLICY_URL: TEST_URL,
        Organization.EULA_URL: TEST_URL,
        Organization.TERM_AND_CONDITION_URL: TEST_URL,
    }


class OrganizationRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/organization_dump.json")]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.organization_route = "/api/extensions/v1beta/organization"

    def setUp(self):
        super().setUp()
        self.test_server.config.server.debugRouter = False
        self.headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        self.unauthorized_headers = self.get_headers_for_token(
            VALID_USER_ID_WITHOUT_MANAGE_ORGANIZATION
        )

    def test_success_create_organization(self):
        rsp = self.flask_client.post(
            self.organization_route,
            json=simple_organization(),
            headers=self.headers,
        )

        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json["id"])

        organization = self.mongo_database["organization"].find_one(
            {Organization.ID_: ObjectId(rsp.json["id"])}
        )
        self.assertTrue(
            isinstance(organization[Organization.CREATE_DATE_TIME], datetime)
        )
        self.assertEqual(
            DashboardId.ORGANIZATION_OVERVIEW.value,
            organization[Organization.DASHBOARD_ID],
        )

    def _validate_legal_files_in_org(self, org_id: str):
        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        organization = self.mongo_database[collection].find_one(
            {Organization.ID_: ObjectId(org_id)}
        )
        for field in legal_docs_s3_fields():
            self.assertEqual(sample_s3_object(), organization[field])

    def test_create_organization_with_legal_document_objects(self):
        payload = {
            **simple_organization(),
            **{key: sample_s3_object() for key in legal_docs_s3_fields()},
        }
        rsp = self.flask_client.post(
            self.organization_route,
            json=payload,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)
        self._validate_legal_files_in_org(rsp.json[Organization.ID])

    def test_failure_create_organization__name_already_exists(self):
        sample_org = simple_organization()
        sample_org[Organization.NAME] = "Test org"
        rsp = self.flask_client.post(
            self.organization_route,
            json=sample_org,
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(
            OrganizationErrorCodes.DUPLICATE_ORGANIZATION_NAME, rsp.json["code"]
        )

    def test_failure_create_organization_with_id(self):
        rsp = self.flask_client.post(
            self.organization_route,
            json={**simple_organization(), "id": INVALID_ORGANIZATION_ID},
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_organization_with_unauthorized_role(self):
        rsp = self.flask_client.post(
            self.organization_route,
            json={**simple_organization(), "id": INVALID_ORGANIZATION_ID},
            headers=self.unauthorized_headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_create_organization_with_invalid_deployment_id(self):
        rsp = self.flask_client.post(
            self.organization_route,
            json={
                **simple_organization(),
                Organization.DEPLOYMENT_IDS: [
                    VALID_DEPLOYMENT_ID,
                    "aa",
                ],
            },
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_organization_no_name(self):
        organization = simple_organization()
        del organization["name"]
        rsp = self.flask_client.post(
            self.organization_route,
            json=organization,
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_organization_no_url(self):
        organization = simple_organization()
        del organization[Organization.TERM_AND_CONDITION_URL]
        rsp = self.flask_client.post(
            self.organization_route,
            json=organization,
            headers=self.headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_success_retrieve_organization(self):
        deployment_id = "5fde855f12db509a2785d899"
        deployment_name = "Deployment X"

        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], VALID_ORGANIZATION_ID)

        expected_deployments_data = {
            DeploymentInfo.ID: deployment_id,
            DeploymentInfo.NAME: deployment_name,
        }
        self.assertEqual(
            rsp.json[OrganizationWithDeploymentInfo.DEPLOYMENTS],
            [expected_deployments_data],
        )

    def test_failure_retrieve_organization_invalid_id(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{INVALID_ORGANIZATION_ID}",
            headers=self.headers,
        )

        self.assertEqual(404, rsp.status_code)
        self.assertEqual(600010, rsp.json["code"])

    def test_failure_retrieve_organization_permission_denied(self):
        # add OrganizationOwner role
        role = {
            RoleAssignment.ROLE_ID: RoleName.ORGANIZATION_OWNER,
            RoleAssignment.RESOURCE: f"organization/{INVALID_ORGANIZATION_ID}",
            RoleAssignment.USER_TYPE: Role.UserType.SUPER_ADMIN,
        }
        self.mongo_database.user.update(
            {"_id": ObjectId(VALID_ACCOUNT_MANAGER_ID)},
            {"$push": {"roles": role}},
        )

        headers = {
            **self.get_headers_for_token(VALID_ACCOUNT_MANAGER_ID),
            AuthorizationMiddleware.ORGANIZATION_HEADER_KEY: INVALID_ORGANIZATION_ID,
        }
        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual("Access of different resources", rsp.json["message"])

    def test_failure_retrieve_organization_with_unauthorized_role(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.unauthorized_headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_success_update_organization(self):
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            json={**simple_organization(), Organization.NAME: "Test Organization"},
            headers=self.headers,
        )

        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], VALID_ORGANIZATION_ID)

        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        organization = self.mongo_database[collection].find_one(
            {Organization.ID_: ObjectId(VALID_ORGANIZATION_ID)}
        )
        self.assertTrue(
            isinstance(organization[Organization.UPDATE_DATE_TIME], datetime)
        )
        self.assertNotIn(Organization.DASHBOARD_ID, organization)

    def test_success_update_org_with_dashboard(self):
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            json={
                **simple_organization(),
                Organization.DASHBOARD_ID: DashboardId.ORGANIZATION_OVERVIEW.value,
            },
            headers=self.headers,
        )

        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            DashboardId.ORGANIZATION_OVERVIEW.value, rsp.json[Organization.DASHBOARD_ID]
        )

    def test_failure_update_organization__name_already_exists(self):
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            json={**simple_organization(), Organization.NAME: "Test org"},
            headers=self.headers,
        )

        self.assertEqual(400, rsp.status_code)
        self.assertEqual(
            OrganizationErrorCodes.DUPLICATE_ORGANIZATION_NAME, rsp.json["code"]
        )

    def test_update_org_name_multiple_times_with_similar_names(self):
        names = [
            "Some New name",
            "Another Some New name",
            "Some New name",
            "Akshay Teraiya 21",
            "Akshay Teraiya 211",
            "Akshay Teraiya 21",
        ]
        for name in names:
            rsp = self.flask_client.put(
                f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
                json={**simple_organization(), Organization.NAME: name},
                headers=self.headers,
            )

            self.assertEqual(200, rsp.status_code)

    def test_success_update_organization_with_url_fields(self):
        dummy_url = "https://someurl2.com"
        body = {
            **simple_organization(),
            Organization.NAME: "Test Organization",
            Organization.PRIVACY_POLICY_URL: dummy_url,
            Organization.EULA_URL: dummy_url,
            Organization.TERM_AND_CONDITION_URL: dummy_url,
        }
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            json=body,
            headers=self.headers,
        )

        self.assertEqual(200, rsp.status_code)

        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        organization = self.mongo_database[collection].find_one(
            {Organization.ID_: ObjectId(VALID_ORGANIZATION_ID)}
        )

        self.assertEqual(organization[Organization.PRIVACY_POLICY_URL], dummy_url)
        self.assertEqual(organization[Organization.EULA_URL], dummy_url)
        self.assertEqual(organization[Organization.TERM_AND_CONDITION_URL], dummy_url)

    def test_success_update_organization_with_legal_document_objects(self):
        body = {
            **simple_organization(),
            Organization.NAME: "Test Organization",
            **{key: sample_s3_object() for key in legal_docs_s3_fields()},
        }
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            json=body,
            headers=self.headers,
        )

        self.assertEqual(200, rsp.status_code)
        self._validate_legal_files_in_org(VALID_ORGANIZATION_ID)

    def test_failure_update_organization_invalid_id(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{INVALID_ORGANIZATION_ID}",
            headers=self.headers,
        )

        self.assertEqual(404, rsp.status_code)
        self.assertEqual(600010, rsp.json["code"])

    def test_failure_update_organization_with_unauthorized_role(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.unauthorized_headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_success_delete_organization(self):
        rsp = self.flask_client.delete(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.headers,
        )

        self.assertEqual(204, rsp.status_code)

    def test_success_delete_organization_role_removed(self):
        user = self.mongo_database.user.find_one(
            {"_id": ObjectId(VALID_ACCOUNT_MANAGER_ID)}
        )
        self.assertEqual(2, len(user["roles"]))
        headers = self.get_headers_for_token(VALID_ACCOUNT_MANAGER_ID)
        rsp = self.flask_client.delete(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}", headers=headers
        )

        self.assertEqual(204, rsp.status_code)
        user = self.mongo_database.user.find_one(
            {"_id": ObjectId(VALID_ACCOUNT_MANAGER_ID)}
        )
        self.assertEqual(1, len(user["roles"]))

    def test_failure_delete_organization_invalid_id(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{INVALID_ORGANIZATION_ID}",
            headers=self.headers,
        )

        self.assertEqual(404, rsp.status_code)
        self.assertEqual(600010, rsp.json["code"])

    def test_failure_delete_organization_with_unauthorized_role(self):
        rsp = self.flask_client.get(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}",
            headers=self.unauthorized_headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def _retrieve_organization_from_db(
        self, organization_id: str = VALID_ORGANIZATION_ID
    ):
        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        return self.mongo_database[collection].find_one(
            {Organization.ID_: ObjectId(organization_id)}
        )

    def test_success_link_a_few_deployments(self):
        db_res_before_changes = self._retrieve_organization_from_db()
        self.assertEqual(1, len(db_res_before_changes[Organization.DEPLOYMENT_IDS]))

        # even though we are passing same deployments, it will push without duplicates
        payload = {
            "deploymentIds": [VALID_DEPLOYMENT_ID, VALID_DEPLOYMENT_ID, DEPLOYMENT_Z]
        }

        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployments",
            headers=self.headers,
            json=payload,
        )

        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            rsp.json[LinkDeploymentsRequestObject.ID], VALID_ORGANIZATION_ID
        )

        db_res_after_changes = self._retrieve_organization_from_db()
        self.assertEqual(3, len(db_res_after_changes[Organization.DEPLOYMENT_IDS]))
        self.assertEqual(4000, db_res_after_changes[Organization.TARGET_CONSENTED])

    def test_success_link_deployment(self):
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployment",
            headers=self.headers,
            json={Organization.DEPLOYMENT_ID: VALID_DEPLOYMENT_ID},
        )

        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], VALID_ORGANIZATION_ID)
        db_res = self._retrieve_organization_from_db()
        self.assertEqual(3000, db_res[Organization.TARGET_CONSENTED])

    def test_success_link_deployment__user_with_multiple_roles(self):
        headers = self.get_headers_for_token(VALID_USER_WITH_MULTIPLE_ROLES)
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployment",
            headers=headers,
            json={Organization.DEPLOYMENT_ID: VALID_DEPLOYMENT_ID},
        )

        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json["id"], VALID_ORGANIZATION_ID)

    def test_failure_link_invalid_deployment(self):
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployment",
            headers=self.headers,
            json={Organization.DEPLOYMENT_ID: INVALID_DEPLOYMENT_ID},
        )

        self.assertEqual(404, rsp.status_code)

    def test_failure_link_deployment_existing_deployment(self):
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployment",
            headers=self.headers,
            json={Organization.DEPLOYMENT_ID: EXISTING_DEPLOYMENT_X},
        )

        self.assertEqual(400, rsp.status_code)
        self.assertEqual(600011, rsp.json["code"])

    def test_failure_link_deployment_existing_deployment_code(self):
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/link-deployment",
            headers=self.headers,
            json={Organization.DEPLOYMENT_ID: DEPLOYMENT_Y},
        )

        self.assertEqual(400, rsp.status_code)
        self.assertEqual(600012, rsp.json["code"])

    def test_success_unlink_deployment(self):
        rsp = self.flask_client.post(
            self.organization_route,
            json=simple_organization(),
            headers=self.headers,
        )
        organization_id = rsp.json["id"]

        self.flask_client.post(
            f"{self.organization_route}/{organization_id}/link-deployment",
            headers=self.headers,
            json={Organization.DEPLOYMENT_ID: VALID_DEPLOYMENT_ID},
        )

        rsp = self.flask_client.delete(
            f"{self.organization_route}/{organization_id}/deployment/{VALID_DEPLOYMENT_ID}",
            headers=self.headers,
        )

        self.assertEqual(204, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.organization_route}/{organization_id}",
            headers=self.headers,
        )

        self.assertNotIn(VALID_DEPLOYMENT_ID, rsp.json[Organization.DEPLOYMENT_IDS])

        # try to unlink same deployment once again, should result in `Deployment is not linked` err
        rsp = self.flask_client.delete(
            f"{self.organization_route}/{organization_id}/deployment/{VALID_DEPLOYMENT_ID}",
            headers=self.headers,
        )

        self.assertEqual(400, rsp.status_code)
        self.assertEqual(OrganizationErrorCodes.DEPLOYMENT_NOT_LINKED, rsp.json["code"])

    def test_success_unlink_deployments(self):
        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        self.mongo_database[collection].update_one(
            {Organization.ID_: ObjectId(VALID_ORGANIZATION_ID)},
            {
                "$addToSet": {
                    Organization.DEPLOYMENT_IDS: {
                        "$each": [VALID_DEPLOYMENT_ID, DEPLOYMENT_Z]
                    }
                }
            },
        )

        db_res_before_changes = self._retrieve_organization_from_db()
        self.assertEqual(3, len(db_res_before_changes[Organization.DEPLOYMENT_IDS]))

        payload = {
            UnlinkDeploymentsRequestObject.DEPLOYMENT_IDS: [
                DEPLOYMENT_Z,
                EXISTING_DEPLOYMENT_X,
            ]
        }
        res = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/unlink-deployments",
            headers=self.headers,
            json=payload,
        )
        self.assertEqual(200, res.status_code)

        db_res_after_changes = self._retrieve_organization_from_db()
        self.assertEqual(1, len(db_res_after_changes[Organization.DEPLOYMENT_IDS]))
        self.assertEqual(3000, db_res_after_changes[Organization.TARGET_CONSENTED])

        # try to unlink same deployment once again, should result in `Deployment is not linked` err
        rsp = self.flask_client.post(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/unlink-deployments",
            headers=self.headers,
            json=payload,
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(OrganizationErrorCodes.DEPLOYMENT_NOT_LINKED, rsp.json["code"])

    def test_failure_unlink_deployment(self):
        rsp = self.flask_client.delete(
            f"{self.organization_route}/{INVALID_ORGANIZATION_ID}/deployment/{VALID_DEPLOYMENT_ID}",
            headers=self.headers,
        )

        self.assertEqual(404, rsp.status_code)
        self.assertEqual(600010, rsp.json["code"])

    def test_failure_delete_deployment_unauthorized_role(self):
        rsp = self.flask_client.delete(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/deployment/{VALID_DEPLOYMENT_ID}",
            headers=self.unauthorized_headers,
        )

        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def get_successful_response_data(self, payload: dict):
        rsp = self.flask_client.post(
            f"{self.organization_route}/search", json=payload, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def test_success_retrieve_organizations(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.NAME_CONTAINS: "",
            RetrieveOrganizationsRequestObject.SORT: [
                {
                    SortField.FIELD: Organization.NAME,
                    SortField.DIRECTION: SortField.Direction.DESC.value,
                }
            ],
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertNotEqual(0, len(rsp_data["items"]))

    def test_success_search_no_results(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.SEARCH_CRITERIA: "abcde",
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertEqual(0, len(rsp_data["items"]))

    def test_success_search_by_name_contains(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.SEARCH_CRITERIA: "Pharmaceuticals",
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertEqual(1, len(rsp_data["items"]))

    def test_success_search_by_id_contains(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.SEARCH_CRITERIA: "5da06",
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertEqual(1, len(rsp_data["items"]))

    def test_success_search_by_status(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.STATUS: [Status.DEPLOYED.value],
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertEqual(1, len(rsp_data["items"]))

    def test_success_search_no_organizations_in_db(self):
        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        self.mongo_database[collection].delete_many({})

        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
        }
        rsp_data = self.get_successful_response_data(data)
        self.assertEqual(0, len(rsp_data["items"]))

    def test_failure_retrieve_organizations_invalid_sort_field(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.NAME_CONTAINS: "",
            RetrieveOrganizationsRequestObject.SORT: [
                {SortField.FIELD: Organization.STATUS, SortField.DIRECTION: "DESC"}
            ],
        }
        rsp = self.flask_client.post(
            f"{self.organization_route}/search", json=data, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_retrieve_organizations_invalid_unauthorized_role(self):
        data = {
            RetrieveOrganizationsRequestObject.SKIP: 0,
            RetrieveOrganizationsRequestObject.LIMIT: 10,
            RetrieveOrganizationsRequestObject.NAME_CONTAINS: "",
            RetrieveOrganizationsRequestObject.SORT: [
                {SortField.FIELD: Organization.STATUS, SortField.DIRECTION: "DESC"}
            ],
        }
        rsp = self.flask_client.post(
            f"{self.organization_route}/search",
            json=data,
            headers=self.unauthorized_headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_success_create_custom_role_organization(self):
        new_roles = [
            {
                Role.NAME: CUSTOM_NEW_ROLE,
                Role.PERMISSIONS: [
                    PermissionType.MANAGE_ORGANIZATION.value,
                    PermissionType.GENERATE_AUTH_TOKEN.value,
                ],
            },
            {
                Role.NAME: f"{CUSTOM_NEW_ROLE} 2",
                Role.PERMISSIONS: [
                    PermissionType.EDIT_ROLE_PERMISSIONS.value,
                ],
            },
        ]

        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/role",
            json={Organization.ROLES: new_roles},
            headers=self.headers,
        )

        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(len(rsp.json["id"]), 2)

        collection = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        organization = self.mongo_database[collection].find_one(
            {Organization.ID_: ObjectId(VALID_ORGANIZATION_ID)}
        )
        self.assertEqual(len(organization["roles"]), 2)

    def test_failure_create_custom_role_without_permission(self):
        new_role = {Role.NAME: CUSTOM_NEW_ROLE, Role.PERMISSIONS: []}

        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/role",
            json={Organization.ROLES: [new_role]},
            headers=self.headers,
        )
        self.assertEqual(rsp.status_code, 403)

    def test_failure_create_two_identical_organization_custom_roles(self):
        new_role = {Role.NAME: "Custom New Role", Role.PERMISSIONS: []}
        rsp = self.flask_client.put(
            f"{self.organization_route}/{VALID_ORGANIZATION_ID}/role",
            json={Organization.ROLES: [new_role, new_role]},
            headers=self.headers,
        )
        self.assertEqual(rsp.status_code, 400)
