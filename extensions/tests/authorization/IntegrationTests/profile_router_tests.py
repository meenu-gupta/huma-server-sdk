import datetime
from datetime import timedelta

from bson import ObjectId
from freezegun import freeze_time
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock


from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import (
    BoardingStatus,
    User,
    UserSurgeryDetails,
    UnseenFlags,
)
from extensions.authorization.router.user_profile_request import (
    OffBoardUserRequestObject,
    RetrieveProfilesRequestObject,
    SortParameters,
)
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import Deployment, Profile, ProfileFields
from extensions.deployment.router.deployment_requests import AddUserNotesRequestObject
from extensions.exceptions import UserErrorCodes
from extensions.kardia.component import KardiaComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.models.primitives.primitive_weight import Weight
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    observation_note,
    weight_result,
    now_str,
    ecg_result,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.adapter.email_adapter import EmailAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
WITHDRAWN_ECONSENT_USER_ID = "62569f29e427af0b5c12779a"
VALID_PROXY_ID = "606eba3a2c94383d620b52ad"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"
VALID_MANAGER_ID = "5e8f0c74b50aa9656c34789d"
VALID_SUPER_ADMIN_ID = "602ce48712b129679a501570"
VALID_SUPPORT_ID = "5ed803dd5f2f99da73655513"
SUPERVISOR_ID = "5ed803dd5f2f99da73655524"
HUMA_SUPPORT_ID = "5ed803dd5f2f99da73675513"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_STAFF_ID = "5ed803dd5f2f99da73654411"
WEIGHT_MODULE_ID = "5f1824ba504787d8d89ebeca"
VALID_NAME = "test"
INVALID_NAME = "invalid"
ECG_SAMPLE_FILE = "ecg_sample"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
CONTRIBUTOR_1_ID_DEPLOYMENT_X = "60071f359e7e44330f732037"
VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT = "600720843111683010a73b4e"
VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT = "6009d2409b0e1f2eab20bbb3"
ACCESS_CONTROLLER_ID = "5ed803dd5f2f99da73654410"
ADMINISTRATOR_ID = "5ed803dd5f2f99da73655514"
CLINICIAN_ID = "5ed803dd5f2f99da73655147"
ORGANIZATION_ID = "5fde855f12db509a2785da06"
ORGANIZATION_EDITOR_ID = "61e6a8e2d9681a389f060848"
ORGANIZATION_OWNER_ID = "61cb194c630781b664bc7eb5"
ORGANIZATION_STAFF = "5ed803dd5f2f99da73654413"
ECG_MODULE_PATH = "extensions.module_result.modules.ecg_module"
PROFILES_USER_ID_1 = VALID_USER_ID
PROFILES_USER_ID_2 = "5e8f0c74b50aa9656c34789c"
PROFILES_USER_ID_3 = "5e8f0c74b50aa9656c34789e"
PROFILES_USER_ID_4 = "5e8f0c74b50aa9656c34779c"
NOT_ONBOARDED_USER_ID = "61fb852583e256e58e7ea9e3"
ORDER = SortParameters.Order
MULTIPLE_DEPLOYMENT_MANAGER_ID = "5e8f0c74b50aa9656c34788d"
ASCENDING = ORDER.ASCENDING.name
DESCENDING = ORDER.DESCENDING.name
ORG_ROLE_USER_IDS = {
    RoleName.ACCESS_CONTROLLER: ACCESS_CONTROLLER_ID,
    RoleName.ORGANIZATION_OWNER: ORGANIZATION_OWNER_ID,
    RoleName.ORGANIZATION_EDITOR: ORGANIZATION_EDITOR_ID,
    RoleName.ORGANIZATION_STAFF: ORGANIZATION_STAFF,
    RoleName.SUPPORT: VALID_SUPPORT_ID,
    RoleName.ADMINISTRATOR: ADMINISTRATOR_ID,
    RoleName.SUPERVISOR: SUPERVISOR_ID,
}


def get_sort_body(field_name, order=DESCENDING):
    return {"sort": {"fields": [field_name], "order": order}}


class ProfileRouterTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        KardiaComponent(),
        OrganizationComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/users_dump.json"),
        Path(__file__).parent.joinpath("fixtures/organization_dump.json"),
    ]
    override_config = {
        "server.deployment.userProfileValidation": "true",
        "server.deployment.offBoarding": "true",
    }

    def setUp(self):
        super().setUp()
        self.email_adapter = MagicMock()

        def bind(binder):
            binder.bind(EmailAdapter, self.email_adapter)

        inject.get_injector().rebind(bind)

        self.headers = self.get_headers_for_token(VALID_USER_ID)
        self.headers_contributor = self.get_headers_for_token(VALID_CONTRIBUTOR_ID)
        self.manager_headers = self.get_headers_for_token(VALID_MANAGER_ID)
        self.super_admin_headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)

        self.base_route = "/api/extensions/v1beta/user"
        self.module_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"
        self.deployment_route = "api/extensions/v1beta/deployment"
        self.staff_route = "api/extensions/v1beta/user/staff"

    def test_success_retrieve_profile(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        user = rsp.json
        self.assertEqual(VALID_USER_ID, user["id"])
        self.assertIn("assignedManagers", user)
        self.assertIn("assignedProxies", user)
        self.assertIn("status", user)
        self.assertNotIn("ragThresholds", user)
        self.assertGreater(len(user["roles"]), 0)

    def test_success_retrieve_user_profile_by_manager(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.manager_headers
        )
        self.assertEqual(200, rsp.status_code)
        user = rsp.json
        self.assertIn("assignedProxies", user)
        self.assertIn("assignedManagers", user)
        self.assertIn("status", user)
        self.assertIn("ragThresholds", user)

    def test_success_retrieve_profile_with_recent_module_results(self):
        module = "Weight"

        for item in [
            weight_result(80, now_str(timedelta(minutes=-1))),
            weight_result(90),
            weight_result(100, now_str(timedelta(days=-1))),
        ]:
            rsp = self.flask_client.post(
                f"{self.module_route}/{module}",
                json=[item],
                headers=self.headers,
                query_string={"moduleConfigId": WEIGHT_MODULE_ID},
            )
            self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.module_route}/{module}",
            json=[weight_result(110, now_str(timedelta(days=-2)))],
            headers=self.headers,
            query_string={"moduleConfigId": WEIGHT_MODULE_ID},
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_USER_ID, rsp.json["id"])

        recent_results = rsp.json["recentModuleResults"]
        weight_data = recent_results.get(WEIGHT_MODULE_ID, None)
        self.assertIsNotNone(weight_data)
        self.assertEqual(len(weight_data), 2)

        item_1 = weight_data[0]
        _, primitive = list(item_1.items())[0]
        self.assertEqual(primitive["value"], 90)

        item_2 = weight_data[-1]
        _, primitive = list(item_2.items())[0]
        self.assertEqual(primitive["value"], 80)

    def test_success_retrieve_profile_with_recent_module_results_invalid_value(self):
        not_valid_weight = 1000

        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_USER_ID, rsp.json["id"])

        recent_results = rsp.json["recentModuleResults"]
        weight_data = recent_results.get(WEIGHT_MODULE_ID, None)
        self.assertIsNotNone(weight_data)
        self.assertEqual(len(weight_data), 1)

        item_1 = weight_data[0]
        _, primitive = list(item_1.items())[0]
        self.assertEqual(primitive["value"], not_valid_weight)

    def test_recent_module_results_proper_sorting(self):
        module = "Weight"

        for item in [
            weight_result(100),
            weight_result(90),
            weight_result(80),
        ]:
            rsp = self.flask_client.post(
                f"{self.module_route}/{module}",
                json=[item],
                headers=self.headers,
                query_string={"moduleConfigId": WEIGHT_MODULE_ID},
            )
            self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )

        recent_results = rsp.json["recentModuleResults"]
        weight_data = recent_results.get(WEIGHT_MODULE_ID, {})

        self.assertEqual(80.0, weight_data[0]["Weight"]["value"])
        self.assertEqual(90.0, weight_data[1]["Weight"]["value"])

    def test_recent_module_results_proper_sorting_and_updated_with_invalid_value(self):
        module = "Weight"

        rsp = self.flask_client.post(
            f"{self.module_route}/{module}",
            json=[weight_result(100)],
            headers=self.headers,
            query_string={"moduleConfigId": WEIGHT_MODULE_ID},
        )
        self.assertEqual(201, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )

        recent_results = rsp.json["recentModuleResults"]
        weight_data = recent_results.get(WEIGHT_MODULE_ID, {})

        self.assertEqual(100.0, weight_data[0]["Weight"]["value"])
        self.assertEqual(1000.0, weight_data[1]["Weight"]["value"])

    @patch(
        "extensions.authorization.services.authorization.AuthorizationService.update_recent_results"
    )
    def test_recent_module_results_not_updated(self, mocked_update_recent_results):
        module = "Weight"

        rsp = self.flask_client.post(
            f"{self.module_route}/{module}",
            json=[weight_result(1000)],
            headers=self.headers,
            query_string={"moduleConfigId": WEIGHT_MODULE_ID},
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])
        mocked_update_recent_results.assert_not_called()

    def test_failure_retrieve_profile_invalid_user(self):
        rsp = self.flask_client.get(
            f"{self.base_route}/{INVALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp.json["code"])

    def test_success_update_profile(self):
        body = {"givenName": "New test name"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(body["givenName"], rsp.json["givenName"])

    def test_success_update_profile_not_editable_field_first_time_update(self):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId(DEPLOYMENT_ID)},
            {
                "$set": {
                    f"{Deployment.PROFILE}.{Profile.FIELDS}.{ProfileFields.UN_EDITABLE_FIELDS}": [
                        "fenlandCohortId"
                    ]
                }
            },
        )
        body = {
            "givenName": "test",
            "familyName": "new test",
            "fenlandCohortId": "10204E",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        body = {
            "givenName": "test",
            "familyName": "new test",
            "fenlandCohortId": "10204F",
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_update_profile_not_editable_field_value_unchanged(self):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId(DEPLOYMENT_ID)},
            {
                "$set": {
                    f"{Deployment.PROFILE}.{Profile.FIELDS}.{ProfileFields.UN_EDITABLE_FIELDS}": [
                        "givenName"
                    ]
                }
            },
        )
        body = {"givenName": "test", "familyName": "new test"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_update_profile_not_editable_field(self):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId(DEPLOYMENT_ID)},
            {
                "$set": {
                    f"{Deployment.PROFILE}.{Profile.FIELDS}.{ProfileFields.UN_EDITABLE_FIELDS}": [
                        "givenName"
                    ]
                }
            },
        )
        body = {"givenName": "New test name"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual("[givenName] field should not be present", rsp.json["message"])

    def test_failure_update_profile_not_editable_ids(self):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId(DEPLOYMENT_ID)},
            {
                "$set": {
                    f"{Deployment.PROFILE}.{Profile.FIELDS}.{ProfileFields.EXTRA_IDS}": {
                        "unEditableIds": ["nhsId"]
                    }
                }
            },
        )
        body = {"nhsId": "testNHSId"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual("[nhsId] field should not be present", rsp.json["message"])

    def test_failure_update_profile_wrong_surgery_date(self):
        body = {User.SURGERY_DATE_TIME: "2000-01-01"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_update_profile_invalid_user(self):
        body = {"givenName": "New test name"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{INVALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp.json["code"])

    def test_failure_update_profile_with_recent_module_results(self):
        body = {"recentModuleResults": {}}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_update_profile_with_email(self):
        body = {"givenName": "New test name", "email": "emailToFail@exmaple.com"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertNotEqual(body["email"], rsp.json["email"])

    def test_failure_update_profile_with_phone_number(self):
        body = {"givenName": "New test name", "phoneNumber": "+38099999988"}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertNotEqual(body["phoneNumber"], rsp.json["phoneNumber"])

    def test_failure_update_profile_with_role(self):
        body = {
            "givenName": "New test name",
            "roles": [{"roleId": "SuperAdmin", "resource": "deployment/*"}],
        }
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertNotEqual(body["roles"], rsp.json["roles"])

    def test_success_update_profile_surgery_details(self):
        body = {User.SURGERY_DETAILS: {UserSurgeryDetails.OPERATION_TYPE: "testKey"}}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body[User.SURGERY_DETAILS], rsp.json[User.SURGERY_DETAILS])

    def test_failure_update_profile_surgery_details_wrong_value(self):
        body = {User.SURGERY_DETAILS: {UserSurgeryDetails.OPERATION_TYPE: "WrongKey"}}
        rsp = self.flask_client.post(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertNotIn(User.SURGERY_DETAILS, rsp.json)

    def test_success_retrieve_profile_with_height_out_of_range(self):
        user_id_with_wrong_height = "601919b5c03550c421c075eb"
        rsp = self.flask_client.get(
            f"{self.base_route}/{user_id_with_wrong_height}",
            headers=self.get_headers_for_token(user_id_with_wrong_height),
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_own_profile_organization_role(self):
        for _, user_id in ORG_ROLE_USER_IDS.items():
            rsp = self.flask_client.get(
                f"{self.base_route}/{user_id}",
                headers=self.get_headers_for_token(user_id),
            )
            self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_patient_profile_organization_role(self):
        accessible_roles = [
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
            RoleName.SUPPORT,
            RoleName.ADMINISTRATOR,
            RoleName.SUPERVISOR,
        ]
        url = f"{self.base_route}/{VALID_USER_ID}"
        for role in accessible_roles:
            headers = {
                "x-deployment-id": DEPLOYMENT_ID,
                **self.get_headers_for_token(ORG_ROLE_USER_IDS.get(role)),
            }
            rsp = self.flask_client.get(url, headers=headers)
            self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_super_admin_profile(self):
        url = f"{self.base_route}/{VALID_SUPER_ADMIN_ID}"
        headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertNotIn("assignedManagers", rsp.json)
        self.assertNotIn("assignedProxies", rsp.json)

    def test_success_retrieve_huma_support_profile(self):
        url = f"{self.base_route}/{HUMA_SUPPORT_ID}"
        headers = self.get_headers_for_token(HUMA_SUPPORT_ID)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertNotIn("assignedManagers", rsp.json)
        self.assertNotIn("assignedProxies", rsp.json)

    def test_failure_retrieve_user_profile_by_huma_support(self):
        url = f"{self.base_route}/{VALID_USER_ID}"
        headers = self.get_headers_for_token(HUMA_SUPPORT_ID)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_manager_profile(self):
        url = f"{self.base_route}/{VALID_MANAGER_ID}"
        headers = self.get_headers_for_token(VALID_MANAGER_ID)
        rsp = self.flask_client.get(url, headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertNotIn("assignedManagers", rsp.json)
        self.assertNotIn("assignedProxies", rsp.json)

    def test_success_retrieve_staff_list(self):
        payload = {"organizationId": ORGANIZATION_ID}
        accessible_role_ids = [
            ACCESS_CONTROLLER_ID,
            ORGANIZATION_STAFF,
        ]
        for role_id in accessible_role_ids:
            rsp = self.flask_client.post(
                f"{self.staff_route}",
                json=payload,
                headers=self.get_headers_for_token(role_id),
            )
            self.assertEqual(10, len(rsp.json))

    def test_success_retrieve_staff_list_common_roles(self):
        payload = {"organizationId": ORGANIZATION_ID}
        accessible_role_ids = [
            ADMINISTRATOR_ID,
            SUPERVISOR_ID,
        ]
        for role_id in accessible_role_ids:
            rsp = self.flask_client.post(
                f"{self.staff_route}",
                json=payload,
                headers=self.get_headers_for_token(role_id),
            )
            self.assertEqual(6, len(rsp.json))

    def test_failure_retrieve_staff_list(self):
        payload = {"organizationId": ORGANIZATION_ID}
        not_accessible_role_ids = [
            VALID_SUPER_ADMIN_ID,
            HUMA_SUPPORT_ID,
            DEPLOYMENT_STAFF_ID,
            VALID_MANAGER_ID,
            ORGANIZATION_EDITOR_ID,
            ORGANIZATION_OWNER_ID,
            VALID_SUPPORT_ID,
        ]
        for role_id in not_accessible_role_ids:
            rsp = self.flask_client.post(
                f"{self.staff_route}",
                json=payload,
                headers=self.get_headers_for_token(role_id),
            )
            self.assertEqual(403, rsp.status_code)

    def test_success_reactivate_user(self):
        self.off_board_user(VALID_USER_ID)
        self.assert_user_off_boarded()

        self.reactivate_user(VALID_USER_ID)
        user = self.get_user(VALID_USER_ID)
        data = user[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.ACTIVE)
        self.assertNotIn(BoardingStatus.REASON_OFF_BOARDED, data)

    def test_failure_reactivate_user_withdrawn(self):
        user_id = WITHDRAWN_ECONSENT_USER_ID
        reactivate_path = f"{self.base_route}/{user_id}/reactivate"
        rsp = self.flask_client.post(reactivate_path, headers=self.headers_contributor)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], UserErrorCodes.WITHDRAWN_ECONSENT)

    def test_success_off_board_user_off_boards_proxy(self):
        self.off_board_user(VALID_USER_ID)
        self.assert_user_off_boarded()

        url = f"{self.base_route}/{VALID_USER_ID}/module-result/Weight/search"
        rsp = self.flask_client.post(
            url, headers=self.get_headers_for_token(VALID_USER_ID)
        )
        self.assertEqual(412, rsp.status_code)

        self.assert_user_off_boarded(VALID_PROXY_ID)

        url = f"{self.base_route}/{VALID_USER_ID}/module-result/Weight/search"
        rsp = self.flask_client.post(
            url, headers=self.get_headers_for_token(VALID_PROXY_ID)
        )
        self.assertEqual(412, rsp.status_code)

    def test_success_off_board_user_off_boards_inactive_proxy_when_onboarded(self):
        url = f"{self.deployment_route}/send-invitation"
        invitation = {
            "emails": ["test@huma.com"],
            "expiresIn": "P1Y",
            "patientId": VALID_USER_ID,
            "roleId": "Proxy",
            "clientId": "ctest1",
            "projectId": "ptest1",
        }
        rsp = self.flask_client.post(
            url, json=invitation, headers=self.get_headers_for_token(VALID_USER_ID)
        )
        self.assertEqual(200, rsp.status_code)
        invitation_id = rsp.json["ids"][0]

        self.off_board_user(VALID_USER_ID)
        self.assert_user_off_boarded()

        invitation = self.mongo_database["invitation"].find_one(
            {"_id": ObjectId(invitation_id)}
        )
        data = {
            "method": 0,
            "email": invitation["email"],
            "validationData": {"invitationCode": invitation["code"]},
            "clientId": "ctest1",
            "projectId": "ptest1",
        }
        rsp = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        self.assertEqual(200, rsp.status_code)
        proxy_id = rsp.json["uid"]

        url = f"{self.base_route}/{VALID_USER_ID}/module-result/Weight/search"
        rsp = self.flask_client.post(
            url, headers=self.get_headers_for_token(VALID_USER_ID)
        )
        self.assertEqual(412, rsp.status_code)

        url = f"{self.base_route}/{VALID_USER_ID}/module-result/Weight/search"
        rsp = self.flask_client.post(url, headers=self.get_headers_for_token(proxy_id))
        self.assertEqual(412, rsp.status_code)

    def test_reactivate_user_correct_button_link_for_signed_out_user(self):
        self.ensure_device_session_exist(VALID_USER_ID)
        self.ensure_device_session_exist(VALID_PROXY_ID)
        self.off_board_user(VALID_USER_ID)
        self.reactivate_user(VALID_USER_ID)

        get_template = self.email_adapter.generate_support_html_with_button
        email_template = get_template.call_args[0][0]

        expected_button_link = "https://iOS.link/login?source=reactivated"
        self.assertEqual(expected_button_link, email_template.buttonLink)

    def assert_user_off_boarded(
        self,
        user_id: str = VALID_USER_ID,
        contributor_id: str = VALID_CONTRIBUTOR_ID,
        reason: int = BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED,
    ):
        user = self.get_user(user_id)
        data = user[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED)
        self.assertEqual(data[BoardingStatus.SUBMITTER_ID], contributor_id)
        self.assertEqual(
            data[BoardingStatus.REASON_OFF_BOARDED],
            reason,
        )

    def ensure_device_session_exist(self, user_id: str):
        self.mongo_database.devicesession.insert(
            {
                "deviceAgent": "Huma/1.0 (com.huma.HumaApp; build:7; iOS 13.5.0) MedopadNetworking/1.0",
                "userId": ObjectId(user_id),
                "refreshToken": None,
                "updateDateTime": datetime.datetime.utcnow(),
                "createDateTime": datetime.datetime.utcnow(),
            }
        )

    def toggle_off_boarding(
        self,
        deployment_id: str = DEPLOYMENT_ID,
        enable: bool = False,
        custom_duration: str = "P1S",
    ):
        body = {
            "features": {"offBoarding": enable},
            "duration": custom_duration,
        }
        rsp = self.flask_client.put(
            f"{self.deployment_route}/{deployment_id}",
            json=body,
            headers=self.super_admin_headers,
        )
        self.assertEqual(200, rsp.status_code)

    def off_board_user(self, user_id: str):
        offboard_path = f"{self.base_route}/{user_id}/offboard"
        data_dict = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: "Recovered"}
        rsp = self.flask_client.post(
            offboard_path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)

    def reactivate_user(self, user_id: str):
        reactivate_path = f"{self.base_route}/{user_id}/reactivate"
        rsp = self.flask_client.post(reactivate_path, headers=self.headers_contributor)
        self.assertEqual(rsp.status_code, 200)

    def get_user(self, user_id: str):
        rsp = self.flask_client.get(
            f"{self.base_route}/{user_id}", headers=self.headers_contributor
        )
        self.assertEqual(rsp.status_code, 200)
        return rsp.json

    def test_success_reactivate_user_extends_study_duration(self):
        self.off_board_user(user_id=VALID_USER_ID)
        self.toggle_off_boarding(enable=True, custom_duration="P1W")
        self.reactivate_user(user_id=VALID_USER_ID)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}/configuration",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertFalse(rsp.json["isOffBoarded"])

        after_a_week = datetime.datetime.utcnow() + timedelta(days=8)
        with freeze_time(after_a_week):
            rsp = self.flask_client.get(
                f"{self.base_route}/{VALID_USER_ID}/configuration",
                headers=self.get_headers_for_token(VALID_USER_ID),
            )
            self.assertTrue(rsp.json["isOffBoarded"])


def profile_sort_request(
    fields: list[str], order: str, skip: int = 0, limit: int = 10, search: str = None
):
    body = {
        "skip": skip,
        "limit": limit,
        RetrieveProfilesRequestObject.SORT: {
            SortParameters.ORDER: order,
            SortParameters.FIELDS: fields,
        },
    }
    if search:
        body[RetrieveProfilesRequestObject.SEARCH] = search
    return body


class ProfilesRouterTests(ExtensionTestCase):
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
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/organization_dump.json"),
        Path(__file__).parent.joinpath("fixtures/unseenrecentresult.json"),
    ]

    def setUp(self):
        super().setUp()
        self._config = self.config_class.get(
            self.config_file_path, self.override_config
        )

        self.headers = self.get_headers_for_token(VALID_MANAGER_ID)

        self.base_route = "/api/extensions/v1beta/user/profiles"
        self.base_route_v1 = "/api/extensions/v1/user/profiles"
        self.module_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"

    def test_success_retrieve_profiles(self):
        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

    def test_success_retrieve_profiles_with_pagination(self):
        rsp = self.flask_client.post(self.base_route_v1, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertIn("total", rsp.json)
        self.assertIn("filtered", rsp.json)
        self.assertEqual(6, rsp.json["filtered"])
        self.assertEqual(6, len(rsp.json["users"]))

    def test_success_retrieve_profiles_with_pagination_and_search(self):
        payload = {"search": VALID_NAME}
        rsp = self.flask_client.post(
            self.base_route_v1, json=payload, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertIn("total", rsp.json)
        self.assertIn("filtered", rsp.json)
        self.assertEqual(3, rsp.json["filtered"])
        self.assertEqual(3, len(rsp.json["users"]))

    def test_success_retrieve_manager_profiles(self):
        rsp = self.flask_client.post(
            self.base_route, json={"role": "Admin"}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json))

    def test_success_retrieve_manager_profiles_with_pagination(self):
        rsp = self.flask_client.post(
            self.base_route_v1, json={"role": "Admin"}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, rsp.json["filtered"])
        self.assertEqual(2, len(rsp.json["users"]))

    def test_success_retrieve_manager_profiles_by_administrator(self):
        roles_to_test = [ADMINISTRATOR_ID, CLINICIAN_ID]
        for role_id in roles_to_test:
            headers = {
                **self.get_headers_for_token(role_id),
                "X-Deployment-Id": DEPLOYMENT_ID,
            }
            rsp = self.flask_client.post(
                self.base_route_v1, json={"role": "Manager"}, headers=headers
            )
            self.assertEqual(200, rsp.status_code)
            self.assertEqual(11, rsp.json["filtered"])
            self.assertEqual(11, len(rsp.json["users"]))

    def test_success_retrieve_all_profiles(self):
        rsp = self.flask_client.post(
            self.base_route, json={"role": None}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_profile_filter_out_service_account(self):
        rsp = self.flask_client.post(
            self.base_route, json={"role": None}, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(20, len(rsp.json))
        for user in rsp.json:
            for role in user["roles"]:
                self.assertNotEqual(Role.UserType.SERVICE_ACCOUNT, role["userType"])

    def test_success_retrieve_profiles_with_search(self):
        body = {"search": VALID_NAME}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json))

    def test_success_retrieve_profiles_with_search_includes_custom_fields(self):
        body = {"search": "944"}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_3, rsp.json[0][User.ID])

        body = {"search": "123ab"}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_1, rsp.json[0][User.ID])

    def test_failure_retrieve_profiles_with_invalid_literal_search(self):
        INVALID_NAME = "\\"
        body = {"search": INVALID_NAME}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json))

    def test_success_retrieve_profiles_with_partial_search(self):
        body = {"search": VALID_NAME[:3]}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json))

    def test_failure_retrieve_profiles_with_invalid_search(self):
        body = {"nameContains": "e"}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

    def test_success_retrieve_profiles_with_fields_filtering(self):
        test_key = "carePlanGroupId"
        cp_croup = "com.huma.covid19.mild"
        body = {"filters": {test_key: cp_croup}}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        wrong_users_array = [u for u in rsp.json if u.get(test_key) != cp_croup]
        self.assertEmpty(wrong_users_array)

    def test_success_retrieve_profiles_with_nested_fields_filtering(self):
        body = {"filters": {"boardingStatus.status": 1}}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json))

        body = {"filters": {"boardingStatus.status": 0}}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json))

    def test_success_retrieve_profiles_sorted_by_boarding_status(self):
        body = get_sort_body(SortParameters.Field.BOARDING_STATUS.name, DESCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json["users"]))
        self.assertEqual(NOT_ONBOARDED_USER_ID, rsp.json["users"][2][User.ID])
        self.assertEqual(PROFILES_USER_ID_3, rsp.json["users"][4][User.ID])

        body = get_sort_body(SortParameters.Field.BOARDING_STATUS.name, ASCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json["users"]))
        self.assertEqual(NOT_ONBOARDED_USER_ID, rsp.json["users"][2][User.ID])
        self.assertEqual(PROFILES_USER_ID_3, rsp.json["users"][4][User.ID])

    def test_success_retrieve_profiles_sorted_by_dob(self):
        body = get_sort_body(SortParameters.Field.DOB.name, DESCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        expected_order = [
            PROFILES_USER_ID_2,
            PROFILES_USER_ID_1,
            NOT_ONBOARDED_USER_ID,
            WITHDRAWN_ECONSENT_USER_ID,
            PROFILES_USER_ID_3,
            PROFILES_USER_ID_4,
        ]
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

        body = get_sort_body(SortParameters.Field.DOB.name, ASCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        expected_order = [
            PROFILES_USER_ID_1,
            PROFILES_USER_ID_2,
            NOT_ONBOARDED_USER_ID,
            PROFILES_USER_ID_3,
            PROFILES_USER_ID_4,
            WITHDRAWN_ECONSENT_USER_ID,
        ]
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

    def test_retrieve_profiles_filter_by_gender(self):
        body = {
            "sort": {"fields": ["FLAGS"], "order": "DESCENDING"},
            "filters": {"gender": "MALE"},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(PROFILES_USER_ID_1, rsp.json["users"][0][User.ID])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][1][User.ID])

        body = {
            "sort": {"fields": ["FLAGS"], "order": "DESCENDING"},
            "filters": {"gender": []},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json["users"]))

    def test_retrieve_profiles_filter_by_gender_and_search_by_name(self):
        body = {
            "sort": {"fields": ["FLAGS"], "order": "DESCENDING"},
            "search": "user",
            "filters": {"gender": "MALE"},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json["users"]))
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][0][User.ID])

    def test_retrieve_profiles_filter_by_details_off_boarded(self):
        field_name = SortParameters.Field.BOARDING_DETAILS_OFF_BOARDED.name
        body = get_sort_body(field_name, DESCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        expected_order = [
            VALID_USER_ID,
            PROFILES_USER_ID_2,
            NOT_ONBOARDED_USER_ID,
            PROFILES_USER_ID_4,
            PROFILES_USER_ID_3,
            WITHDRAWN_ECONSENT_USER_ID,
        ]

        self.assertEqual(200, rsp.status_code)
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

    def test_retrieve_profiles_filter_by_details_off_boarded_ascending(self):
        field_name = SortParameters.Field.BOARDING_DETAILS_OFF_BOARDED.name
        body = get_sort_body(field_name, ASCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        expected_order = [
            VALID_USER_ID,
            PROFILES_USER_ID_2,
            NOT_ONBOARDED_USER_ID,
            WITHDRAWN_ECONSENT_USER_ID,
            PROFILES_USER_ID_3,
            PROFILES_USER_ID_4,
        ]

        self.assertEqual(200, rsp.status_code)
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

    def test_retrieve_profiles_sort_desc_by_reason_off_boarded(self):
        field_name = SortParameters.Field.BOARDING_REASON_OFF_BOARDED.name
        body = get_sort_body(field_name, DESCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        expected_order = [
            VALID_USER_ID,
            PROFILES_USER_ID_2,
            NOT_ONBOARDED_USER_ID,
            WITHDRAWN_ECONSENT_USER_ID,
            PROFILES_USER_ID_3,
            PROFILES_USER_ID_4,
        ]

        self.assertEqual(200, rsp.status_code)
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

    def test_retrieve_profiles_sort_asc_by_reason_off_boarded(self):
        field_name = SortParameters.Field.BOARDING_REASON_OFF_BOARDED.name
        body = get_sort_body(field_name, ASCENDING)
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        expected_order = [
            VALID_USER_ID,
            PROFILES_USER_ID_2,
            NOT_ONBOARDED_USER_ID,
            PROFILES_USER_ID_4,
            PROFILES_USER_ID_3,
            WITHDRAWN_ECONSENT_USER_ID,
        ]

        self.assertEqual(200, rsp.status_code)
        actual_order = [user[User.ID] for user in rsp.json["users"]]
        self.assertEqual(expected_order, actual_order)

    def test_retrieve_profiles_sort_by_weight(self):
        module_config_id = "5f1824ba504787d8d89ebeca"
        module_id = "Weight"
        body = {
            "sort": {
                "fields": ["MODULE"],
                "extra": {
                    "moduleConfigId": module_config_id,
                    "moduleId": module_id,
                },
            }
        }

        # DESCENDING
        body["sort"]["order"] = "DESCENDING"
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        user_1, user_2 = rsp.json["users"][:2]
        value_1 = user_1["recentModuleResults"][module_config_id][0][module_id]["value"]
        value_2 = user_2["recentModuleResults"][module_config_id][0][module_id]["value"]
        self.assertGreater(value_1, value_2)

        # ASCENDING
        body["sort"]["order"] = "ASCENDING"
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        user_1, user_2 = rsp.json["users"][:2]
        value_1 = user_1["recentModuleResults"][module_config_id][0][module_id]["value"]
        value_2 = user_2["recentModuleResults"][module_config_id][0][module_id]["value"]
        self.assertLess(value_1, value_2)

    def test_retrieve_profiles_filter_by_dob(self):
        body = {
            "sort": {"fields": ["FLAGS"], "order": "DESCENDING"},
            "filters": {"dateOfBirth": {"gte": "1994-10-10", "lte": "2000-12-01"}},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(PROFILES_USER_ID_1, rsp.json["users"][0][User.ID])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][1][User.ID])

        body = {
            "filters": {"dateOfBirth": {"gte": "2000-10-10"}},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(WITHDRAWN_ECONSENT_USER_ID, rsp.json["users"][0][User.ID])

    def test_retrieve_profiles_filter_by_surgery_date(self):
        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "filters": {"surgeryDateTime": {"gte": "2010-01-10"}},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json["users"]))
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][0][User.ID])

        body = {
            "filters": {"surgeryDateTime": {"lte": "2010-01-10"}},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json["users"]))
        self.assertEqual(PROFILES_USER_ID_1, rsp.json["users"][0][User.ID])

    def test_retrieve_profiles_filter_by_status(self):
        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "filters": {"tags": ["flagged"]},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json["users"]))
        self.assertEqual(1, rsp.json["filtered"])
        self.assertEqual(6, rsp.json["total"])

        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "filters": {"tags": ["flagged", "inpatient"]},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(2, rsp.json["filtered"])
        self.assertEqual(6, rsp.json["total"])

        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "filters": {"tags": []},
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        users_without_tag = rsp.json["filtered"]
        all_users = rsp.json["total"]

        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "filters": {
                "tags": [
                    "flagged",
                    "inpatient",
                    "continueMonitoring",
                    "deceased",
                    "needsAdmission",
                    "recovered",
                ]
            },
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        users_with_tag = rsp.json["filtered"]
        self.assertEqual(all_users, users_with_tag + users_without_tag)

    def test_retrieve_profiles_filter_by_manager_id(self):
        body = {
            "sort": {"fields": ["LAST_UPDATED"], "order": "DESCENDING"},
            "managerId": VALID_MANAGER_ID,
        }
        rsp = self.flask_client.post(
            self.base_route_v1, json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(2, rsp.json["filtered"])
        self.assertEqual(6, rsp.json["total"])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][0][User.ID])
        self.assertIn(VALID_MANAGER_ID, rsp.json["users"][0]["assignedManagers"])

    def test_retrieve_profiles_by_manager_id_does_not_return_not_common_users(self):
        body = {
            "managerId": MULTIPLE_DEPLOYMENT_MANAGER_ID,
        }
        headers = self.get_headers_for_token(VALID_MANAGER_ID)
        rsp = self.flask_client.post(self.base_route_v1, json=body, headers=headers)
        # have to see all the manager's users
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json["users"]))
        self.assertEqual(0, rsp.json["filtered"])
        self.assertEqual(6, rsp.json["total"])

    def test_retrieve_profiles_by_manager_id_returns_common_users(self):
        body = {
            "managerId": VALID_MANAGER_ID,
        }
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID)
        rsp = self.flask_client.post(self.base_route_v1, json=body, headers=headers)
        # have to see all the manager's users
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json["users"]))
        self.assertEqual(2, rsp.json["filtered"])
        self.assertEqual(8, rsp.json["total"])
        self.assertEqual(PROFILES_USER_ID_1, rsp.json["users"][0][User.ID])
        self.assertIn(VALID_MANAGER_ID, rsp.json["users"][0]["assignedManagers"])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json["users"][1][User.ID])
        self.assertIn(VALID_MANAGER_ID, rsp.json["users"][1]["assignedManagers"])

    def test_retrieve_profiles_with_pagination(self):
        # 1. Skip only
        body = {"skip": 1}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(5, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_2, rsp.json[0][User.ID])
        self.assertEqual(NOT_ONBOARDED_USER_ID, rsp.json[2][User.ID])
        self.assertEqual(PROFILES_USER_ID_3, rsp.json[3][User.ID])

        # 2. Limit only
        body = {"limit": 2}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_1, rsp.json[0][User.ID])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json[1][User.ID])

        # 2. Skip + Limit
        body = {"limit": 1, "skip": 1}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_2, rsp.json[0][User.ID])

        # 3. search
        body = {"search": "user"}
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json))
        self.assertEqual(PROFILES_USER_ID_2, rsp.json[0][User.ID])

        # 4. sort and search
        body = profile_sort_request(["GIVEN_NAME"], "ASCENDING", limit=5, search="est")
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json))
        self.assertListEqual(
            ["test", "test2", "test2"], [u[User.GIVEN_NAME] for u in rsp.json]
        )

        # 5. search nhsId
        body = profile_sort_request(
            ["GIVEN_NAME"], "ASCENDING", limit=5, search="nhs_id"
        )
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json))

        # 6. search nhsId and sort on RAG
        body = profile_sort_request(["RAG"], "ASCENDING", limit=5, search="nhs_id")
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json))

    def test_retrieve_profiles_with_task_percentage_sort(self):
        body = profile_sort_request(["TASK_COMPLIANCE"], "DESCENDING", limit=2)
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(PROFILES_USER_ID_4, rsp.json[0][User.ID])
        self.assertEqual(PROFILES_USER_ID_3, rsp.json[1][User.ID])

    def test_retrieve_profiles_with_task_percentage_sort_ascending(self):
        body = profile_sort_request(["TASK_COMPLIANCE"], "ASCENDING", limit=2)
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(WITHDRAWN_ECONSENT_USER_ID, rsp.json[0][User.ID])
        self.assertEqual(PROFILES_USER_ID_1, rsp.json[1][User.ID])

    def test_retrieve_profiles_with_any_sort_includes_flags_column(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        body = profile_sort_request(["LAST_UPDATED"], "DESCENDING", limit=2)
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        for user in rsp.json:
            self.assertIn(User.FLAGS, user)

        body = profile_sort_request(["FLAGS"], "DESCENDING", limit=2)
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        for user in rsp.json:
            self.assertIn(User.FLAGS, user)

    def test_retrieve_profiles_with_flags(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "ASCENDING",
                SortParameters.FIELDS: ["FLAGS"],
            }
        }
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))
        self.assertNotIn(User.FLAGS, rsp.json[0])
        self.assertNotIn(User.FLAGS, rsp.json[1])
        self.assertIn(User.FLAGS, rsp.json[4])
        self.assertEqual(1, rsp.json[5][User.FLAGS][UnseenFlags.GRAY])
        empty_flags = {UnseenFlags.RED: 0, UnseenFlags.AMBER: 0, UnseenFlags.GRAY: 0}
        # sort the results by flags to check the order
        responses = [
            (user[User.ID], user[User.FLAGS] if User.FLAGS in user else empty_flags)
            for user in rsp.json
        ]
        sorted_result = list(responses)
        sorted_result.sort(
            key=lambda x: (
                x[1][UnseenFlags.RED],
                x[1][UnseenFlags.AMBER],
                x[1][UnseenFlags.GRAY],
            )
        )
        self.assertListEqual(sorted_result, responses)

    def test_retrieve_profiles_with_flags_sorting_ignores_disabled_modules(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        self.config.server.deployment.flagsEnabled = True
        body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "DESCENDING",
                SortParameters.FIELDS: ["FLAGS"],
            }
        }
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))
        # Even though user 2 has combined flag count greater than user 1,
        # since disabled modules are ignored for sorting user 1 appears
        # at top.
        self.assertEqual(PROFILES_USER_ID_1, rsp.json[0][User.ID])
        self.assertEqual(PROFILES_USER_ID_2, rsp.json[1][User.ID])

    def test_retrieve_profiles_with_flags_sorting_ignores_excluded_modules(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        self.config.server.deployment.flagsEnabled = True
        body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "DESCENDING",
                SortParameters.FIELDS: ["FLAGS"],
            }
        }
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        self.assertEqual(PROFILES_USER_ID_2, rsp.json[1][User.ID])
        self.assertEqual({"red": 1, "amber": 0, "gray": 0}, rsp.json[1][User.FLAGS])

    def test_retrieve_profiles_with_flags_after_submitting_module_results(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        retrieve_profiles_body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "DESCENDING",
                SortParameters.FIELDS: ["FLAGS"],
            }
        }
        rsp = self.flask_client.post(
            self.base_route, json=retrieve_profiles_body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        users = rsp.json
        users_unseen_flags_count = {}
        sample_module_results = [
            self.sample_module_result_with_red_flag(),
            self.sample_module_result_with_amber_flag(),
            self.sample_module_result_with_gray_flag(),
        ]
        profile_user_ids = [PROFILES_USER_ID_1]
        empty_flags = {UnseenFlags.RED: 0, UnseenFlags.AMBER: 0, UnseenFlags.GRAY: 0}
        for user in users:
            user_id = user.get(User.ID)
            if user_id not in profile_user_ids:
                continue
            users_unseen_flags_count[user_id] = user.get(User.FLAGS) or empty_flags
            for module_result in sample_module_results:
                self.create_module_result(user_id, module_result[0], [module_result[1]])

        rsp = self.flask_client.post(
            self.base_route, json=retrieve_profiles_body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        users = rsp.json
        for user in users:
            user_id = user.get(User.ID)
            if user_id not in profile_user_ids:
                continue
            user_new_flags = user.get(User.FLAGS) or empty_flags
            for (flag, flag_count) in user_new_flags.items():
                self.assertEqual(
                    users_unseen_flags_count[user_id][flag] + 1, flag_count
                )

    def test_retrieve_profiles_with_flags_after_submitting_observation_note(self):
        self.apply_migration(self.db_migration_path, self._config, force_apply=True)
        retrieve_profiles_body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "DESCENDING",
                SortParameters.FIELDS: ["FLAGS"],
            }
        }
        rsp = self.flask_client.post(
            self.base_route, json=retrieve_profiles_body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        users = rsp.json
        user = next(filter(lambda user: user.get(User.ID) == PROFILES_USER_ID_1, users))
        user_flags = user.get(User.FLAGS)
        self.assertIsNotNone(user_flags)
        self.add_user_note(user.get(User.ID), "note")

        rsp = self.flask_client.post(
            self.base_route, json=retrieve_profiles_body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        users = rsp.json
        user = next(filter(lambda user: user.get(User.ID) == PROFILES_USER_ID_1, users))
        user_flags = user.get(User.FLAGS)
        self.assertIsNone(user_flags)

    @staticmethod
    def sample_weight_module_result() -> dict:
        return {
            "type": Weight.__name__,
            "moduleConfigId": "5f1824ba504787d8d89ebeca",
            "deviceName": "iOS",
            "deploymentId": DEPLOYMENT_ID,
            "startDateTime": now_str(),
            "value": 100,
        }

    def sample_module_result_with_red_flag(self):
        sample_data = self.sample_weight_module_result()
        sample_data["value"] = 200
        return ("Weight", sample_data)

    def sample_module_result_with_amber_flag(self):
        sample_data = self.sample_weight_module_result()
        sample_data["value"] = 110
        return ("Weight", sample_data)

    def sample_module_result_with_gray_flag(self):
        sample_data = self.sample_weight_module_result()
        sample_data["value"] = 80
        return ("Weight", sample_data)

    def create_module_result(self, user_id: str, module_name: str, data: list):
        rsp = self.flask_client.post(
            f"{self.module_route}/{module_name}",
            json=data,
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(201, rsp.status_code)

    def add_user_note(self, user_id: str, note: str):
        headers = self.get_headers_for_token(VALID_MANAGER_ID)
        request_object = AddUserNotesRequestObject(note=note)
        rsp = self.flask_client.post(
            f"/api/extensions/v1/user/{user_id}/deployment/{DEPLOYMENT_ID}/notes",
            json=request_object.to_dict(),
            headers=headers,
        )
        self.assertEqual(201, rsp.status_code)

    def test_retrieve_profiles_with_flags_and_stats(self):
        body = {
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.ORDER: "ASCENDING",
                SortParameters.FIELDS: ["FLAGS"],
                SortParameters.STATUS: ["FLAGGED"],
            }
        }
        rsp = self.flask_client.post(self.base_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))
        users = rsp.json
        self.assertIn("flagged", users[0]["tags"])

    def test_validation_error_on_non_positive_limit(self):
        request = {
            RetrieveProfilesRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            RetrieveProfilesRequestObject.SEARCH: "est",
            RetrieveProfilesRequestObject.SORT: {
                SortParameters.FIELDS: ["GIVEN_NAME"],
                SortParameters.ORDER: "ASCENDING",
            },
            RetrieveProfilesRequestObject.LIMIT: 0,
        }
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveProfilesRequestObject.from_dict(request)

    def test_retrieve_profiles_status_correct(self):
        rsp = self.flask_client.post(
            f"{self.module_route}/Weight",
            json=[weight_result(80, now_str(timedelta(days=-1)))],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        height = {
            "type": "Height",
            "deviceName": "iOS",
            "deploymentId": DEPLOYMENT_ID,
            "startDateTime": now_str(timedelta(days=-1)),
            "value": 180,
        }

        rsp = self.flask_client.post(
            f"{self.module_route}/Height", json=[height], headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.module_route}/Questionnaire",
            json=[observation_note()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        body = rsp.json
        user = next(filter(lambda x: x["id"], body), None)
        self.assertIsNotNone(user)

        for status_data in user["status"].values():
            for status in status_data.values():
                self.assertTrue(status["seen"])

        rsp = self.flask_client.post(
            f"{self.module_route}/Weight",
            json=[weight_result(80, now_str(timedelta(days=1)))],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        body = rsp.json
        user = next(filter(lambda x: x["id"], body), None)
        self.assertIsNotNone(user)

        for status_data in user["status"].values():
            for name, status in status_data.items():
                if name == "Weight":
                    self.assertFalse(status["seen"])
                else:
                    self.assertTrue(status["seen"])

    def test_not_able_to_submit_observation_notes_for_proxy(self):
        proxy_id = "606eba3a2c94383d620b52ad"
        module_route = f"/api/extensions/v1beta/user/{proxy_id}/module-result"
        rsp = self.flask_client.post(
            f"{module_route}/Questionnaire",
            json=[observation_note()],
            headers=self.get_headers_for_token(proxy_id),
        )
        self.assertEqual(404, rsp.status_code)

    def test_proxy_user_not_able_to_retrieve_linked_user_observation_notes(self):
        proxy_id = "606eba3a2c94383d620b52ad"
        module_name = Questionnaire.__name__

        module_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"
        rsp = self.flask_client.post(
            f"{module_route}/Questionnaire",
            json=[observation_note()],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        # trying to get an observation note as proxy
        search_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result/{module_name}/search"
        rsp = self.flask_client.post(
            search_route,
            headers=self.get_headers_for_token(proxy_id),
        )
        self.assertEqual(0, len(rsp.json[module_name]))

    def test_failure_set_below_min_range_height(self):
        height = {
            "type": "Height",
            "deviceName": "iOS",
            "deploymentId": DEPLOYMENT_ID,
            "startDateTime": now_str(timedelta(days=-1)),
            "value": 99,
        }

        rsp = self.flask_client.post(
            f"{self.module_route}/Height", json=[height], headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_set_greater_max_range_height(self):
        height = {
            "type": "Height",
            "deviceName": "iOS",
            "deploymentId": DEPLOYMENT_ID,
            "startDateTime": now_str(timedelta(days=-1)),
            "value": 251,
        }

        rsp = self.flask_client.post(
            f"{self.module_route}/Height", json=[height], headers=self.headers
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_retrieve_profiles_by_contributor(self):
        rsp = self.flask_client.post(
            self.base_route,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_retrieve_profiles_by_custom_role_with_manage_patient_data(self):
        rsp = self.flask_client.post(
            self.base_route,
            json={"deploymentId": DEPLOYMENT_ID},
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_MANAGE_PATIENT
            ),
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_retrieve_profiles_by_custom_role_without_manage_patient_data(
        self,
    ):
        rsp = self.flask_client.post(
            self.base_route,
            json={"deploymentId": DEPLOYMENT_ID},
            headers=self.get_headers_for_token(
                VALID_CUSTOM_ROLE_ID_WITH_OUT_MANAGE_PATIENT
            ),
        )
        self.assertEqual(403, rsp.status_code)

    @patch(f"{ECG_MODULE_PATH}.ecg_healthkit.ECGHealthKitService", MagicMock())
    def check_ecg_threshold_color(self, value, color):
        path = Path(__file__).parent.joinpath(f"fixtures/{ECG_SAMPLE_FILE}")
        with open(path, "rb") as ecg_file:
            file_data = ecg_file.read()
        data = {
            "filename": ECG_SAMPLE_FILE,
            "mime": "application/octet-stream",
            "file": (BytesIO(file_data), "file"),
        }
        rsp = self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )

        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(
            f"{self.module_route}/ECGHealthKit",
            json=[ecg_result(value)],
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)

        body = rsp.json
        user = next(filter(lambda x: x["id"], body), None)
        for item in user["ragThresholds"]:
            item_data = user["ragThresholds"][item]
            if "ECGHealthKit" in item_data:
                self.assertEqual(item_data["ECGHealthKit"]["value"]["color"], color)

    def test_success_color_CBEBF0_for_ecg_thresholds(self):
        self.check_ecg_threshold_color(1, "#CBEBF0")

    def test_success_color_FBCCD7_for_ecg_thresholds(self):
        for i in range(2, 4):
            self.check_ecg_threshold_color(i, "#FBCCD7")

    def test_success_color_FFDA9F_for_ecg_thresholds(self):
        values_to_check = [6, 8]
        for value in values_to_check:
            self.check_ecg_threshold_color(value, "#FFDA9F")

    def test_success_retrieve_profiles_organization_role(self):
        accessible_roles = [
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
            RoleName.SUPPORT,
            RoleName.ADMINISTRATOR,
        ]
        for role in accessible_roles:
            rsp = self.flask_client.post(
                self.base_route,
                json={"deploymentId": DEPLOYMENT_ID},
                headers=self.get_headers_for_token(ORG_ROLE_USER_IDS.get(role)),
            )
            self.assertEqual(200, rsp.status_code)

    def test_failure_retrieve_profiles_by_support_role_different_org(self):
        rsp = self.flask_client.post(
            self.base_route,
            json={"deploymentId": "61dfe4ed306d9822167e9ad4"},
            headers=self.get_headers_for_token(VALID_SUPPORT_ID),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_profiles_organization_custom_role(self):
        custom_role_user = "61920aa2b39e8acfb70a761c"
        organization_id = "5fde855f12db509a2785da06"

        headers = self.get_headers_for_token(custom_role_user)
        headers.update({"x-org-id": organization_id})

        rsp = self.flask_client.post(
            self.base_route, json={"deploymentId": DEPLOYMENT_ID}, headers=headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_retrieve_profiles_organization_role_no_deployment_id(self):
        rsp = self.flask_client.post(
            self.base_route,
            headers=self.get_headers_for_token(ORGANIZATION_STAFF),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_profiles_all_data(self):
        rsp = self.flask_client.post(self.base_route, headers=self.headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

    def test_success_retrieve_profiles_only_patient_identifiers(self):
        only_fields = [
            User.NHS,
            User.DATE_OF_BIRTH,
            User.EMAIL,
            User.GIVEN_NAME,
            User.FAMILY_NAME,
            User.ID,
        ]
        body = {"patientIdentifiersOnly": True}
        rsp = self.flask_client.post(self.base_route, headers=self.headers, json=body)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        for item in rsp.json:
            for field in only_fields:
                self.assertIn(field, item)
            self.assertEqual(len(item.keys()), 6)

    def test_success_retrieve_managers_no_restrictions(self):
        body = {"patientDataOnly": True, "role": Role.UserType.MANAGER}
        rsp = self.flask_client.post(self.base_route, headers=self.headers, json=body)
        self.assertEqual(200, rsp.status_code)

        for item in rsp.json:
            self.assertIn(User.GIVEN_NAME, item)

        # count number of org level staff
        count = 0
        for item in rsp.json:
            if "organization/" in item["roles"][0]["resource"]:
                count = count + 1

        self.assertEqual(5, count)

    def test_success_retrieve_managers_no_restrictions_by_organization_staff(self):
        body = {"role": Role.UserType.MANAGER}
        headers = {
            **self.get_headers_for_token(ORGANIZATION_STAFF),
            "X-Deployment-Id": DEPLOYMENT_ID,
        }
        rsp = self.flask_client.post(self.base_route, headers=headers, json=body)
        self.assertEqual(200, rsp.status_code)

        for item in rsp.json:
            self.assertIn(User.GIVEN_NAME, item)

    def test_success_retrieve_users_hidden_names_by_organization_staff(self):
        headers = {
            **self.get_headers_for_token(ORGANIZATION_STAFF),
            "X-Deployment-Id": DEPLOYMENT_ID,
        }
        rsp = self.flask_client.post(self.base_route, headers=headers)
        self.assertEqual(200, rsp.status_code)

        for item in rsp.json:
            self.assertNotIn(User.GIVEN_NAME, item)
            self.assertNotIn(User.FAMILY_NAME, item)

    def test_failure_retrieve_users_patient_data_only_by_organization_staff(self):
        body = {"patientIdentifiersOnly": True}
        headers = {
            **self.get_headers_for_token(ORGANIZATION_STAFF),
            "X-Deployment-Id": DEPLOYMENT_ID,
        }
        rsp = self.flask_client.post(self.base_route, headers=headers, json=body)
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_profiles_only_patient_data(self):
        only_fields = [
            User.NHS,
            User.DATE_OF_BIRTH,
            User.EMAIL,
            User.GIVEN_NAME,
            User.FAMILY_NAME,
            User.ID,
        ]
        body = {"patientDataOnly": True}
        rsp = self.flask_client.post(self.base_route, headers=self.headers, json=body)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json))

        for item in rsp.json:
            for field in only_fields:
                self.assertNotIn(field, item)

    def test_sort_by_last_updated_descending(self):
        for order in (ORDER.ASCENDING, ORDER.DESCENDING):
            body = {
                "sort": {
                    "fields": ["LAST_UPDATED"],
                    "order": order.value,
                }
            }
            rsp = self.flask_client.post(
                self.base_route, headers=self.headers, json=body
            )
            self.assertEqual(200, rsp.status_code)

            reverse = order == ORDER.DESCENDING
            properly_sorted_list = rsp.json.copy()
            properly_sorted_list.sort(
                key=lambda u: u.get(User.LAST_SUBMIT_DATE_TIME), reverse=reverse
            )

            for i, user in enumerate(properly_sorted_list):
                self.assertDictEqual(user, rsp.json[i])

    def test_sort_profiles_by_deployment_id(self):
        order = ORDER.DESCENDING
        body = {
            "sort": {
                "fields": ["DEPLOYMENT_ID"],
                "order": order.value,
            }
        }
        rsp = self.flask_client.post(self.base_route, headers=self.headers, json=body)
        self.assertEqual(200, rsp.status_code)

        last_profile = rsp.json[-1]
        self.assertEqual(NOT_ONBOARDED_USER_ID, last_profile[User.ID])


class DeleteUserTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/users_dump.json"),
    ]

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(VALID_SUPER_ADMIN_ID)

        self.base_route = "/api/extensions/v1beta/user"

    def test_success_user_delete(self):
        path = f"{self.base_route}/{VALID_USER_ID}/delete-user"
        rsp = self.flask_client.delete(path, headers=self.headers)
        self.assertEqual(204, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER_ID}", headers=self.headers
        )
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp.json["code"])

    def test_failure_delete_user_by_huma_support(self):
        path = f"{self.base_route}/{VALID_USER_ID}/delete-user"
        headers = self.get_headers_for_token(HUMA_SUPPORT_ID)
        rsp = self.flask_client.delete(path, headers=headers)
        self.assertEqual(403, rsp.status_code)

    def test_success_user_delete_primitives(self):
        module_res_path = f"/api/extensions/v1beta/user/{VALID_USER_ID}/module-result"
        rsp = self.flask_client.post(
            f"{module_res_path}/Weight/search",
            json={},
            headers=self.headers,
        )
        self.assertTrue(len(rsp.json["Weight"]))

        del_user_path = f"{self.base_route}/{VALID_USER_ID}/delete-user"
        rsp = self.flask_client.delete(del_user_path, headers=self.headers)
        self.assertEqual(rsp.status_code, 204)

        rsp = self.flask_client.post(
            f"{module_res_path}/Weight/search",
            json={},
            headers=self.headers,
        )
        self.assertEqual(UserErrorCodes.INVALID_USER_ID, rsp.json["code"])
