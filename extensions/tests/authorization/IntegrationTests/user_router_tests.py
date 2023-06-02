from io import BytesIO
from unittest.mock import patch

from bson import ObjectId
from flask import g

from extensions.authorization.exceptions import WrongActivationOrMasterKeyException
from extensions.authorization.callbacks import setup_storage_auth
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import AdditionalContactDetails, User
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveFullConfigurationResponseObject as ResponseObject,
    RetrieveUserResourcesResponseObject,
)
from extensions.deployment.models.deployment import (
    Deployment,
    Features,
    Messaging,
    Profile,
    ProfileFields,
)
from extensions.deployment.models.learn import (
    Learn,
    LearnSection,
    LearnArticle,
    LearnArticleContent,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive
from .abstract_permission_test_case import AbstractPermissionTestCase
from extensions.organization.models.organization import Organization
from extensions.organization.repository.mongo_organization_repository import (
    MongoOrganizationRepository,
)
from extensions.tests.authorization.IntegrationTests.profile_router_tests import (
    ORGANIZATION_STAFF,
    DEPLOYMENT_ID,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    MANAGER_2_ID_DEPLOYMENT_X,
    get_medication,
    get_journal,
    TEST_FILE_NAME,
    content_test_file,
    BUCKET_NAME,
    get_sign_up_data,
    get_sample_preferred_units,
    get_sample_additional_contact_details,
    TEST_FILE_PATH,
    get_service_account_signup_data,
    DEPLOYMENT_X_USER_CODE,
    DEPLOYMENT_X_MANAGER_CODE,
    MANAGER_1_ID_DEPLOYMENT_X,
    MANAGER_2_ID_DEPLOYMENT_Y,
    USER_1_ID_DEPLOYMENT_X,
    USER_2_ID_DEPLOYMENT_X,
    CUSTOM_ROLE_1_ID_DEPLOYMENT_X,
    USER_1_ID_DEPLOYMENT_Y,
    SUPER_ADMIN_ID,
    USER_ID_WITH_VIEW_IDENTIFIER,
    USER_ID_WITH_OUT_VIEW_IDENTIFIER,
    CONTRIBUTOR_1_ID_DEPLOYMENT_X,
    DEPLOYMENT_2_ID,
    CUSTOM_ROLE_2_ID_DEPLOYMENT_X,
    ORGANIZATION_STAFF_ID,
    DEPLOYMENT_STAFF_ID,
    USER_WITHOUT_ROLE,
    DEPLOYMENT_CODE,
    weight_result,
    CORRECT_MASTER_KEY,
    WRONG_MASTER_KEY,
)
from extensions.tests.deployment.UnitTests.test_helpers import (
    sample_s3_object,
    legal_docs_url_fields,
)
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    VIEW,
    USER_VIEW,
)
from extensions.tests.video_call.IntegrationTests.video_call_router_tests import (
    mocked_create_room,
    ADAPTER_PATH as TWILIO_ADAPTER,
    SERVICE_PATH as TWILIO_SERVICE,
)
from extensions.twilio_video.service.video_service import TwilioVideoService
from sdk.auth.enums import Method
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import SignUpRequestObject
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Language
from sdk.common.utils.common_functions_utils import find
from sdk.storage.callbacks.binder import PostStorageSetupEvent


PREDEFINED_MESSAGE = "Great job! Keep up the good work."


class BaseCRUDPermissionTestCase(AbstractPermissionTestCase):
    def setUp(self):
        super().setUp()
        self.base_path = "/api/extensions/v1beta/user"
        self.full_config_path = "/api/extensions/v1beta/user/%s/fullconfiguration"

    def assertUserInDb(self, user: dict):
        db_user = self.mongo_database["user"].find_one({"_id": ObjectId(user["id"])})
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user["givenName"], user["userAttributes"]["givenName"])
        self.assertEqual(db_user["familyName"], user["userAttributes"]["familyName"])
        self.assertEqual(db_user["email"], user["email"])


class UserCRUDPermissionTestCase(BaseCRUDPermissionTestCase):
    """
    - two deployments: X, Y
    - two users / manager for deployment X: user1, user2, manager1, manager2
    - one users / manager for deployment Y: user3, manager3
    - super admin can create deployment or admin_data
    - user or manager can't create deployment or admin_data
    """

    def get_user_from_db(self, user_id: str = USER_1_ID_DEPLOYMENT_X):
        return self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})

    def upload_test_file_by_user(self, filename, user_id):
        # preparing request data
        data = {
            "filename": filename,
            "mime": "application/yaml",
            "file": (BytesIO(content_test_file()), "file"),
        }
        # returning response
        return self.flask_client.post(
            f"/api/storage/v1beta/upload/{BUCKET_NAME}",
            data=data,
            headers=self.get_headers_for_token(user_id),
            content_type="multipart/form-data",
        )

    def test_successful_create_user(self):
        # creating user
        user = get_sign_up_data("user1@example.com", "user1", DEPLOYMENT_X_USER_CODE)
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)

        self.assertUserInDb({**user, "id": user_id})

        # creating manager
        manager = get_sign_up_data(
            "manager1@example.com", "manager1", DEPLOYMENT_X_MANAGER_CODE
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=manager)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)

        self.assertUserInDb({**manager, "id": user_id})

    def test_successful_create_user_with_enrollment_id(self):
        for i in range(1, 5):
            user = get_sign_up_data(
                f"user{i}@example.com", f"user{i}", DEPLOYMENT_X_USER_CODE
            )
            rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user)
            user_id = rsp.json["uid"]
            self.assertIsNotNone(user_id)

            user = self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
                {User.ID_: ObjectId(user_id)}
            )

            enrollment_number = user[User.ENROLLMENT_ID]
            self.assertEqual(enrollment_number, i)

            deployment = self.mongo_database[
                MongoDeploymentRepository.DEPLOYMENT_COLLECTION
            ].find_one({Deployment.ID_: ObjectId(DEPLOYMENT_ID)})
            self.assertEqual(deployment[Deployment.ENROLLMENT_COUNTER], i)

    def test_enrollment_number_update_abort(self):
        user = get_sign_up_data(f"user1@example.com", f"user1", DEPLOYMENT_X_USER_CODE)
        self.flask_client.post(f"{self.auth_route}/signup", json=user)

        deployment = self.mongo_database[
            MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        ].find_one({Deployment.ID_: ObjectId(DEPLOYMENT_ID)})
        self.assertEqual(deployment[Deployment.ENROLLMENT_COUNTER], 1)

        self.flask_client.post(f"{self.auth_route}/signup", json=user)

        deployment = self.mongo_database[
            MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        ].find_one({Deployment.ID_: ObjectId(DEPLOYMENT_ID)})
        self.assertEqual(deployment[Deployment.ENROLLMENT_COUNTER], 1)

    def test_successful_retrieve_user_with_enrollment_number(self):
        user = get_sign_up_data(f"user1@example.com", f"user1", DEPLOYMENT_X_USER_CODE)
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)

        rsp = self.flask_client.get(
            f"{self.base_path}/{user_id}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        enrollment_id = rsp.json[User.ENROLLMENT_ID]
        self.assertIsNotNone(enrollment_id)
        self.assertEqual(
            rsp.json[User.ENROLLMENT_NUMBER],
            f"{DEPLOYMENT_CODE}-{str(enrollment_id).zfill(4)}",
        )

    def test_retrieve_profiles_with_enrollment_number(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/profiles",
            headers={
                **self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_Y),
            },
        )
        self.assertEqual(200, rsp.status_code)

        users = rsp.json
        for user in users:
            self.assertIn(User.ENROLLMENT_NUMBER, user)

    def test_failure_retrieve_profiles__wrong_dt_format_in_filter(self):
        payload = {
            RetrieveProfilesRequestObject.FILTERS: {
                User.DATE_OF_BIRTH: {
                    "gte": "2018-11-22T18:29:59Z",
                    "lte": "1992-03-17T18:30:00Z",
                }
            },
        }
        rsp = self.flask_client.post(
            f"{self.base_path}/profiles",
            headers={
                **self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_Y),
            },
            json=payload,
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_retrieve_profiles__with_labels_filter(self):

        rsp = self._successfully_retrieve_users_with_label_filters(
            ["5d386cc6ff885918d96edb2c"]
        )
        self.assertEqual(3, len(rsp.json))

        rsp = self._successfully_retrieve_users_with_label_filters(
            ["5e8eeae1b707216625ca4202"]
        )
        self.assertEqual(2, len(rsp.json))

        rsp = self._successfully_retrieve_users_with_label_filters(
            ["5d386cc6ff885918d96edb2c", "5e8eeae1b707216625ca4202"]
        )
        self.assertEqual(3, len(rsp.json))

    def test_success_retrieve_profiles__with_empty_labels_filter(self):

        rsp = self._successfully_retrieve_users_with_label_filters([])
        self.assertEqual(7, len(rsp.json))

    def test_failure_retrieve_profiles__with_invalid_labels_filter(self):

        rsp = self._retrieve_users_with_label_filters(["errtsf"])
        self.assertEqual(403, rsp.status_code)
        self.assertEqual("Invalid label id in ['errtsf']", rsp.json["message"])

    def test_failure_retrieve_profiles__with_empty_string_labels_filter(self):

        rsp = self._retrieve_users_with_label_filters([" "])
        self.assertEqual(403, rsp.status_code)
        self.assertEqual("Invalid label id in [' ']", rsp.json["message"])

    def test_successful_sign_up_with_email_password(self):
        # User sign up
        data = get_sign_up_data("user1@example.com", "user1", DEPLOYMENT_X_USER_CODE)
        data[SignUpRequestObject.METHOD] = Method.EMAIL_PASSWORD.value
        data[SignUpRequestObject.PASSWORD] = "Aa123456"
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=data)
        self.assertIsNotNone(rsp.json["uid"])

        # Manager sign up
        data = get_sign_up_data(
            "manager1@example.com", "manager1", DEPLOYMENT_X_MANAGER_CODE
        )
        data[SignUpRequestObject.METHOD] = Method.EMAIL_PASSWORD
        data[SignUpRequestObject.PASSWORD] = "Aa123456"
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=data)
        self.assertIsNotNone(rsp.json["uid"])

    def test_successful_create_service_account(self):
        data = get_service_account_signup_data(
            "test", "Exporter", DEPLOYMENT_X_USER_CODE, CORRECT_MASTER_KEY
        )
        rsp = self.flask_client.post(f"{self.auth_route}/service-account", json=data)
        self.assertIsNotNone(rsp.json["authId"])
        self.assertIsNotNone(rsp.json["authKey"])
        self.assertEqual(rsp.status_code, 201)

    def test_fail_create_service_account(self):
        data = get_service_account_signup_data(
            "test", "Exporter", DEPLOYMENT_X_USER_CODE, WRONG_MASTER_KEY
        )
        rsp = self.flask_client.post(f"{self.auth_route}/service-account", json=data)
        self.assertEqual(
            rsp.json["message"], WrongActivationOrMasterKeyException().debug_message
        )
        self.assertEqual(rsp.status_code, 400)

    def test_success_user_device_register(self):
        not_verified_user_id = "6034bfa242276aaded6ad685"
        body = {
            "devicePushId": "TEST_DEVICE_PUSH_ID_1",
            "devicePushIdType": "IOS_APNS",
        }
        rsp = self.flask_client.post(
            "/api/notification/v1beta/device/register",
            headers=self.get_headers_for_token(not_verified_user_id),
            json=body,
        )
        self.assertEqual(201, rsp.status_code)

    def test_retrieve_profile(self):
        # successful by owner
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # successful by manager of same deployment
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # successful by contributor of same deployment
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # successful by custom role of same deployment
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            query_string={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # failure by another user
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_2_ID_DEPLOYMENT_X}",
            query_string={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure retrieve profile by manager of another deployment
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_Y}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure by super admin
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(SUPER_ADMIN_ID),
        )
        self.assertEqual(403, rsp.status_code)

    def test_retrieve_profile_with_view_identifier_permission(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers={
                **self.get_headers_for_token(USER_ID_WITH_VIEW_IDENTIFIER),
                "x-deployment-id": DEPLOYMENT_ID,
            },
        )

        self.assertIn(User.GIVEN_NAME, rsp.json)
        self.assertIn(User.FAMILY_NAME, rsp.json)

    def test_retrieve_profile_without_view_identifier_permission(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers={
                **self.get_headers_for_token(USER_ID_WITH_OUT_VIEW_IDENTIFIER),
                "x-deployment-id": DEPLOYMENT_ID,
            },
        )

        self.assertNotIn(User.GIVEN_NAME, rsp.json)
        self.assertNotIn(User.FAMILY_NAME, rsp.json)

    def test_retrieve_profiles_with_view_identifier_permission(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/profiles",
            headers={
                **self.get_headers_for_token(USER_ID_WITH_VIEW_IDENTIFIER),
                "x-deployment-id": DEPLOYMENT_ID,
            },
        )

        users = rsp.json
        for user in users:
            self.assertIn(User.GIVEN_NAME, user)
            self.assertIn(User.FAMILY_NAME, user)

    def test_retrieve_profiles_without_view_identifier_permission(self):
        rsp = self.flask_client.post(
            f"{self.base_path}/profiles",
            headers={
                **self.get_headers_for_token(USER_ID_WITH_OUT_VIEW_IDENTIFIER),
                "x-deployment-id": DEPLOYMENT_ID,
            },
        )

        users = rsp.json
        for user in users:
            self.assertNotIn(User.GIVEN_NAME, user)
            self.assertNotIn(User.FAMILY_NAME, user)

    def test_update_profile(self):
        body = {"height": 185}
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(body["height"], rsp.json["height"])

    def test_update_profile_with_additional_contact_details(self):
        body = get_sample_additional_contact_details()
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertDictEqual(
            body[User.ADDITIONAL_CONTACT_DETAILS],
            rsp.json[User.ADDITIONAL_CONTACT_DETAILS],
        )

    def test_failure_additional_contact_details_invalid_phone_number(self):
        body = get_sample_additional_contact_details()
        body[User.ADDITIONAL_CONTACT_DETAILS].update(
            {AdditionalContactDetails.REGULAR_CONTACT_NUMBER: "1234567812"}
        )
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_additional_contact_details_missing_are_not_required(self):
        field_keys = [
            AdditionalContactDetails.REGULAR_CONTACT_NAME,
            AdditionalContactDetails.REGULAR_CONTACT_NUMBER,
            AdditionalContactDetails.EMERGENCY_CONTACT_NAME,
            AdditionalContactDetails.EMERGENCY_CONTACT_NUMBER,
        ]

        for key in field_keys:
            body = get_sample_additional_contact_details()
            del body[User.ADDITIONAL_CONTACT_DETAILS][key]
            rsp = self.flask_client.post(
                f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
                json=body,
                headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
            )
            self.assertEqual(200, rsp.status_code)

    def test_failure_additional_contact_details_empty_field(self):
        field_keys = [
            AdditionalContactDetails.ALT_CONTACT_NUMBER,
            AdditionalContactDetails.REGULAR_CONTACT_NAME,
            AdditionalContactDetails.EMERGENCY_CONTACT_NAME,
        ]

        for key in field_keys:
            body = get_sample_additional_contact_details()
            body[User.ADDITIONAL_CONTACT_DETAILS].update({key: ""})
            rsp = self.flask_client.post(
                f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
                json=body,
                headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
            )
            self.assertEqual(403, rsp.status_code)

    def test_create_medication(self):
        # successful by user for himself
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/medication/",
            json=get_medication(USER_1_ID_DEPLOYMENT_X),
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # failure by another user
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_2_ID_DEPLOYMENT_X}/medication/",
            json=get_medication(USER_2_ID_DEPLOYMENT_X),
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure by super admin
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/medication/",
            json=get_medication(USER_1_ID_DEPLOYMENT_X),
            headers=self.get_headers_for_token(SUPER_ADMIN_ID),
        )
        self.assertEqual(403, rsp.status_code)

        # failure by manager
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/medication/",
            json=get_medication(USER_1_ID_DEPLOYMENT_X),
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # failure by manager of another deployment
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_Y}/medication/",
            json=get_medication(USER_1_ID_DEPLOYMENT_Y),
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_create_module_results_without_startDateTime(self):
        primitive = get_journal(DEPLOYMENT_ID)
        primitive.pop(Primitive.START_DATE_TIME)
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Journal",
            json=[primitive],
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)
        stored_primitive_id = rsp.json["ids"][0]

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/primitive/Journal/{stored_primitive_id}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

    def test_create_module_results(self):
        # successful by user for himself
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Journal",
            json=[get_journal(DEPLOYMENT_ID)],
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # successful by manager
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Journal",
            json=[get_journal(DEPLOYMENT_ID)],
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # failure by another user
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_2_ID_DEPLOYMENT_X}/module-result/Journal",
            json=[get_journal(DEPLOYMENT_ID)],
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure by super admin
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Journal",
            json=[get_journal(DEPLOYMENT_ID)],
            headers=self.get_headers_for_token(SUPER_ADMIN_ID),
        )
        self.assertEqual(403, rsp.status_code)

        # failure by manager of another deployment
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_Y}/module-result/Journal",
            json=[get_journal(DEPLOYMENT_ID)],
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_unsuccessful_create_module_results_with_wrong_primitive(self):
        primitive_data = get_journal(DEPLOYMENT_ID)
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Weight",
            json=[primitive_data],
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(404, rsp.status_code)

    def test_unsuccessful_create_module_results_with_wrong_primitives(self):
        primitive_data = [get_journal(DEPLOYMENT_ID), weight_result(80, DEPLOYMENT_ID)]
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/module-result/Weight",
            json=primitive_data,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(404, rsp.status_code)

    def _get_profiles(self, headers: dict, body: dict):
        url = f"/api/extensions/v1beta/user/profiles"
        return self.flask_client.post(
            url,
            json=body,
            headers=headers,
        )

    def test_failure_retrieve_profiles_negative_limit(self):
        headers = self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X)
        json = {
            self.DEPLOYMENT_KEY: DEPLOYMENT_ID,
            RetrieveProfilesRequestObject.LIMIT: -1,
        }
        rsp = self._get_profiles(headers, json)
        self.assertEqual(403, rsp.status_code)

    def test_failure_retrieve_profiles_negative_skip(self):
        headers = self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X)
        json = {
            self.DEPLOYMENT_KEY: DEPLOYMENT_ID,
            RetrieveProfilesRequestObject.SKIP: -1,
        }
        rsp = self._get_profiles(headers, json)
        self.assertEqual(403, rsp.status_code)

    def test_successful_retrieve_profiles(self):
        headers = self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X)
        url = f"/api/extensions/v1beta/user/profiles"
        json = {self.DEPLOYMENT_KEY: DEPLOYMENT_ID}
        rsp = self._get_profiles(headers, json)
        self.assertEqual(200, rsp.status_code)
        ids = [u["id"] for u in rsp.json]
        self.assertTrue(USER_1_ID_DEPLOYMENT_X in ids)
        self.assertTrue(USER_2_ID_DEPLOYMENT_X in ids)
        self.assertFalse(USER_1_ID_DEPLOYMENT_Y in ids)

        # contributor
        headers = self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X)

        rsp = self.flask_client.post(url, json=json, headers=headers)
        self.assertEqual(200, rsp.status_code)
        ids = [u["id"] for u in rsp.json]
        self.assertTrue(USER_1_ID_DEPLOYMENT_X in ids)
        self.assertTrue(USER_2_ID_DEPLOYMENT_X in ids)
        self.assertFalse(USER_1_ID_DEPLOYMENT_Y in ids)

        # custom role
        headers = self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X)

        rsp = self.flask_client.post(url, json=json, headers=headers)
        self.assertEqual(200, rsp.status_code)
        ids = [u["id"] for u in rsp.json]
        self.assertTrue(USER_1_ID_DEPLOYMENT_X in ids)
        self.assertTrue(USER_2_ID_DEPLOYMENT_X in ids)
        self.assertFalse(USER_1_ID_DEPLOYMENT_Y in ids)

        # manager2
        headers = self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_Y)
        rsp = self.flask_client.post(
            url, json={self.DEPLOYMENT_KEY: DEPLOYMENT_2_ID}, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        ids = [u["id"] for u in rsp.json]
        self.assertFalse(USER_1_ID_DEPLOYMENT_X in ids)
        self.assertFalse(USER_2_ID_DEPLOYMENT_X in ids)
        self.assertTrue(USER_1_ID_DEPLOYMENT_Y in ids)

    def test_setting_context_to_g(self):
        with self.test_app.app_context():
            headers = self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X)

            self.flask_client.post(
                f"/api/extensions/v1beta/user/profiles", json={}, headers=headers
            )
            self.assertEqual(type(g.authz_user), AuthorizedUser)
            self.assertEqual(type(g.user), User)
            self.assertEqual(type(g.auth_user), AuthUser)

    def test_failure_retrieve_profiles_with_user(self):
        headers = self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X)

        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/profiles", json={}, headers=headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_successful_super_admin_upload_for_deployment_and_user_can_read(self):
        filename = f"deployment/{DEPLOYMENT_ID}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, SUPER_ADMIN_ID)
        self.assertEqual(rsp.status_code, 201)

        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{BUCKET_NAME}/{filename}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith("text/html"))

    def test_failure_super_admin_upload_file_for_deployment(self):
        filename = f"x/{DEPLOYMENT_ID}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, SUPER_ADMIN_ID)
        self.assertEqual(rsp.status_code, 403)

    def test_success_user_or_manager_read_write_for_photo(self):
        filename = f"user/{USER_1_ID_DEPLOYMENT_X}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, USER_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 201)

        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{BUCKET_NAME}/{filename}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith("text/html"))
        self.assertTrue(str(rsp.data.decode("utf-8")).startswith("http://"))

        filename = f"user/{USER_1_ID_DEPLOYMENT_X}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, MANAGER_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 201)

        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{BUCKET_NAME}/{filename}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith("text/html"))
        self.assertTrue(str(rsp.data.decode("utf-8")).startswith("http://"))

    def test_failure_user_or_manager_read_write_for_another_user(self):
        # upload user1 data by user2
        filename = f"user/{USER_2_ID_DEPLOYMENT_X}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, USER_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 403)

        # download user1 data by user2
        filename = f"user/{USER_1_ID_DEPLOYMENT_X}/{TEST_FILE_NAME}"
        self.upload_test_file_by_user(filename, USER_1_ID_DEPLOYMENT_X)
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{BUCKET_NAME}/{filename}",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(rsp.status_code, 403)

    def test_failure_user_write_for_super_admin_or_random_place(self):
        # same deployment
        filename = f"deployment/{DEPLOYMENT_ID}/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, USER_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 403)

        # random place
        filename = f"x/{TEST_FILE_NAME}"
        rsp = self.upload_test_file_by_user(filename, USER_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 400)

    def test_retrieve_revere_results(self):
        # success manager of same deployment retrieve all user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/all/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # success manager of same deployment retrieve finished user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # success user retrieve own finished tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        # failure user retrieve all his revere tests (including not finished)
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/all/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure manager of another deployment receive all user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/all/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure user of another deployment receive all user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/all/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure user of same deployment receive all user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_2_ID_DEPLOYMENT_X}/revere-test/all/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure manager of another deployment receive finished user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure user of another deployment receive finished user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # failure user of same deployment receive finished user's tests
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{USER_2_ID_DEPLOYMENT_X}/revere-test/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_revere_only_owner_can_start_test(self):
        # owner can start test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/start/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # manager can't start test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/start/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # manager of another deployment can't start test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/start/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # another user can't start test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/start/",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user from another deployment can't start test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/start/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_Y),
        )
        self.assertEqual(403, rsp.status_code)

    def test_revere_only_owner_can_upload_results(self):
        # creating test
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/start/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        test_id = rsp.json["id"]
        words_list_id = rsp.json["wordLists"][0]["id"]

        # manager can't upload result
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/{test_id}/words/{words_list_id}/audio/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # manager of another deployment can't upload result
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/revere-test/{test_id}/words/{words_list_id}/audio/",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # another user can't upload result
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/{test_id}/words/{words_list_id}/audio/",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user from another deployment can't upload result
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/revere-test/{test_id}/words/{words_list_id}/audio/",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_Y),
        )
        self.assertEqual(403, rsp.status_code)

    @patch(f"{TWILIO_ADAPTER}.create_room", mocked_create_room)
    def test_video_call_can_be_initiated_by_manager_only(self):
        url_template = "/api/extensions/v1beta/manager/{}/video/user/{}/initiate"

        # admin can initiate call to user of same deployment
        rsp = self.flask_client.post(
            url_template.format(MANAGER_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_X),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # contributor can initiate call to user of same deployment
        rsp = self.flask_client.post(
            url_template.format(CONTRIBUTOR_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_X),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # custom role with contact patient permission can initiate call to user of same deployment
        rsp = self.flask_client.post(
            url_template.format(CUSTOM_ROLE_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_X),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(201, rsp.status_code)

        # custom role with out contact patient permission cannot initiate call to user of same deployment
        rsp = self.flask_client.post(
            url_template.format(CUSTOM_ROLE_2_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_X),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(CUSTOM_ROLE_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # manager can't initiate call to user of another deployment
        rsp = self.flask_client.post(
            url_template.format(MANAGER_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_Y),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user can't initiate call to user of another deployment
        rsp = self.flask_client.post(
            url_template.format(USER_1_ID_DEPLOYMENT_X, USER_1_ID_DEPLOYMENT_Y),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user can't initiate call to user of same deployment
        rsp = self.flask_client.post(
            url_template.format(USER_1_ID_DEPLOYMENT_X, USER_2_ID_DEPLOYMENT_X),
            json={self.DEPLOYMENT_KEY: DEPLOYMENT_ID},
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    @patch("twilio.request_validator.RequestValidator.validate")
    def test_twilio_callbacks_only_for_twilio(self, mock_twilio_validate):
        # when request not valid
        mock_twilio_validate.return_value = False
        rsp = self.flask_client.post(f"/api/extensions/v1beta/video/callbacks")
        self.assertEqual(403, rsp.status_code)

        # when request valid
        mock_twilio_validate.return_value = True
        rsp = self.flask_client.post(f"/api/extensions/v1beta/video/callbacks")
        self.assertEqual(200, rsp.status_code)

    def test_export_allowed_only_for_manager_of_same_deployment(self):
        data = {VIEW: USER_VIEW}
        # manager can export data from own deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(200, rsp.status_code)

        # contributor can export data from own deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(200, rsp.status_code)

        # custom role with export deployment can export data from own deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(CUSTOM_ROLE_1_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(200, rsp.status_code)

        # custom role with out export deployment cannot export data from own deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(CUSTOM_ROLE_2_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(403, rsp.status_code)

        # user can't export data from own deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(403, rsp.status_code)

        # user can't export another deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_ID}",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(403, rsp.status_code)

        # manager can't export another deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/export/deployment/{DEPLOYMENT_2_ID}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
            json=data,
        )
        self.assertEqual(403, rsp.status_code)

    @patch(f"{TWILIO_ADAPTER}.create_room", mocked_create_room)
    @patch(f"{TWILIO_ADAPTER}.complete_room")
    @patch(f"{TWILIO_SERVICE}.send_user_push_notification_call_ended")
    def test_video_call_can_be_completed_by_participants_only(
        self, mocked_push, mocked_complete_room
    ):
        video_call_sid, video_call_id = TwilioVideoService().create_room(
            manager_id=MANAGER_1_ID_DEPLOYMENT_X, user_id=USER_1_ID_DEPLOYMENT_X
        )

        # user can complete own video call
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/video/{video_call_id}/complete",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        mocked_push.assert_not_called()
        mocked_complete_room.assert_called_once()
        mocked_complete_room.reset_mock()

        # call's manager can complete call
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/manager/{MANAGER_1_ID_DEPLOYMENT_X}/video/{video_call_id}/complete",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        mocked_push.assert_called_once()
        mocked_complete_room.assert_called_once()

        # call's manager can't complete call to user of another deployment
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_Y}/video/{video_call_id}/complete",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user can't complete video call for other user
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/user/{USER_1_ID_DEPLOYMENT_X}/video/{video_call_id}/complete",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

        # user can't complete video call for manager
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/manager/{MANAGER_1_ID_DEPLOYMENT_X}/video/{video_call_id}/complete",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def test_retrieve_user_configuration(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json[Deployment.ONBOARDING_CONFIGS]))
        self.assertEqual(8, len(rsp.json[Deployment.MODULE_CONFIGS]))
        self.assertGreater(len(rsp.json[Deployment.CONTACT_US_URL]), 1)
        self.assertEqual(
            [PREDEFINED_MESSAGE],
            rsp.json[Deployment.FEATURES][Features.MESSAGING][Messaging.MESSAGES],
        )

        self._verify_article_content_url(rsp.json)

        # check if licensed questionnaire modules has been populated
        modules = rsp.json[Deployment.MODULE_CONFIGS]
        for module in modules:
            # EQ5
            if module[ModuleConfig.ID] == "5d386cc6ff885918d96edb4a":
                self.assertEqual(8, len(module[ModuleConfig.CONFIG_BODY]["pages"]))

    def _retrieve_legal_docs_urls_from_deployment(self, deployment_id: str) -> dict:
        coll_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        res = self.mongo_database[coll_name].find_one(
            {Deployment.ID_: ObjectId(deployment_id)}
        )
        return {
            Deployment.EULA_URL: res[Deployment.EULA_URL],
            Deployment.TERM_AND_CONDITION_URL: res[Deployment.TERM_AND_CONDITION_URL],
            Deployment.PRIVACY_POLICY_URL: res[Deployment.PRIVACY_POLICY_URL],
        }

    def _remove_legal_docs_urls_and_set_file_objects(self, deployment_id: str):
        coll_name = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        self.mongo_database[coll_name].update_one(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$set": {
                    Deployment.PRIVACY_POLICY_OBJECT: sample_s3_object(),
                    Deployment.PRIVACY_POLICY_URL: None,
                    Deployment.TERM_AND_CONDITION_OBJECT: sample_s3_object(),
                    Deployment.TERM_AND_CONDITION_URL: None,
                    Deployment.EULA_OBJECT: sample_s3_object(),
                    Deployment.EULA_URL: None,
                }
            },
        )

    def test_user_configuration__legal_docs_urls_are_already_set(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        expected_urls = self._retrieve_legal_docs_urls_from_deployment(DEPLOYMENT_ID)
        for key, url in expected_urls.items():
            self.assertEqual(url, rsp.json.get(key))

    def test_user_configuration__legal_urls_should_be_generated(self):
        initial_docs_urls = self._retrieve_legal_docs_urls_from_deployment(
            DEPLOYMENT_ID
        )
        self._remove_legal_docs_urls_and_set_file_objects(DEPLOYMENT_ID)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        for legal_doc_url_field in legal_docs_url_fields():
            self.assertNotEqual(
                initial_docs_urls[legal_doc_url_field], rsp.json[legal_doc_url_field]
            )

    def test_user_configuration__profile_fields_ordering_prefilled(self):
        update_url = f"api/extensions/v1beta/deployment/{DEPLOYMENT_ID}"
        update_data = {
            Deployment.PROFILE: {
                Profile.FIELDS: {ProfileFields.ORDERING: [ProfileFields.GENDER_OPTIONS]}
            }
        }
        rsp = self.flask_client.put(
            update_url,
            json=update_data,
            headers=self.get_headers_for_token(SUPER_ADMIN_ID),
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        profile_data = rsp.json.get("profile", {}).get("fields", {}).get("ordering")
        self.assertIsInstance(profile_data, list)
        self.assertEqual(len(profile_data), len(ProfileFields.get_orderable_fields()))
        self.assertEqual(profile_data[0], ProfileFields.GENDER_OPTIONS)

    def test_failure_user_with_star_in_resource_configuration(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{SUPER_ADMIN_ID}/configuration",
            headers=self.get_headers_for_token(SUPER_ADMIN_ID),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(rsp.json["code"], ErrorCodes.FORBIDDEN_ID)

    def test_success_finished_onboarding(self):
        self.mongo_database["user"].update_one(
            {"_id": ObjectId(USER_1_ID_DEPLOYMENT_X)},
            {"$unset": {User.FINISHED_ONBOARDING: ""}},
        )
        user_dict = self.get_user_from_db()
        self.assertNotIn(User.FINISHED_ONBOARDING, user_dict)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        user_dict = self.get_user_from_db()
        self.assertTrue(user_dict[User.FINISHED_ONBOARDING])

    def test_success_update_profile_with_preferred_units(self):
        body = get_sample_preferred_units()
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertDictEqual(body[User.PREFERRED_UNITS], rsp.json[User.PREFERRED_UNITS])

    def test_failure_update_profile_with_preferred_units_with_invalid_module(self):
        body = get_sample_preferred_units()
        body[User.PREFERRED_UNITS].update({"PeakFlow": "L/min"})
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_update_profile_with_preferred_units_with_invalid_unit(self):
        body = get_sample_preferred_units()
        body[User.PREFERRED_UNITS].update({"Weight": "kgg"})
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}",
            json=body,
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(400, rsp.status_code)

    def test_success_retrieve_manager_configuration(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{MANAGER_1_ID_DEPLOYMENT_X}/configuration",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(10, len(rsp.json[Deployment.MODULE_CONFIGS]))
        self.assertGreater(len(rsp.json[Deployment.CONTACT_US_URL]), 1)

    def test_retrieve_user_full_configuration_legal_docs_s3_obj_are_empty(self):
        user_id = "61fb852583e256e58e7ea9e1"
        headers = self.get_headers_for_token(user_id)
        rsp = self.flask_client.get(self.full_config_path % user_id, headers=headers)
        self.assertEqual(200, rsp.status_code)

    def test_retrieve_user_full_configuration_user(self):
        headers = self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X)
        rsp = self.flask_client.get(
            self.full_config_path % USER_1_ID_DEPLOYMENT_X, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json[ResponseObject.ORGANIZATIONS]))
        self.assertEqual(1, len(rsp.json[ResponseObject.DEPLOYMENTS]))

        expected_urls = self._retrieve_legal_docs_urls_from_deployment(DEPLOYMENT_ID)
        deployment_data = rsp.json[ResponseObject.DEPLOYMENTS][0]
        for key, url in expected_urls.items():
            self.assertEqual(url, deployment_data.get(key))
        self._verify_article_content_url(deployment_data)

        # check if licensed questionnaire modules has been populated
        modules = deployment_data[Deployment.MODULE_CONFIGS]
        for module in modules:
            # EQ5
            if module[ModuleConfig.ID] == "5d386cc6ff885918d96edb4a":
                self.assertEqual(8, len(module[ModuleConfig.CONFIG_BODY]["pages"]))
                self.assertIn(ModuleConfig.ABOUT, module)
                self.assertIn(ModuleConfig.NOTIFICATION_DATA, module)

    def _verify_article_content_url(self, deployment: dict):
        learn_sections = deployment[Deployment.LEARN][Learn.SECTIONS]
        article = learn_sections[0][LearnSection.ARTICLES][-1]
        self.assertIn(LearnArticleContent.URL, article[LearnArticle.CONTENT])
        self.assertIsNotNone(article[LearnArticle.CONTENT][LearnArticleContent.URL])

    def test_user_full_configuration__legal_urls_should_be_generated(self):
        initial_docs_urls = self._retrieve_legal_docs_urls_from_deployment(
            DEPLOYMENT_ID
        )
        self._remove_legal_docs_urls_and_set_file_objects(DEPLOYMENT_ID)

        headers = self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X)
        rsp = self.flask_client.get(
            self.full_config_path % USER_1_ID_DEPLOYMENT_X, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        deployment_data = rsp.json[ResponseObject.DEPLOYMENTS][0]

        for legal_doc_url_field in legal_docs_url_fields():
            self.assertNotEqual(
                initial_docs_urls[legal_doc_url_field],
                deployment_data[legal_doc_url_field],
            )

    def test_retrieve_admin_full_configuration_user(self):
        headers = self.get_headers_for_token(SUPER_ADMIN_ID)
        rsp = self.flask_client.get(
            self.full_config_path % SUPER_ADMIN_ID, headers=headers
        )
        self.assertEqual(403, rsp.status_code)

    def test_full_configuration_legal_docs__org_urls_are_already_set(self):
        headers = self.get_headers_for_token(ORGANIZATION_STAFF_ID)
        rsp = self.flask_client.get(
            self.full_config_path % ORGANIZATION_STAFF_ID, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        organization = rsp.json[ResponseObject.ORGANIZATIONS][0]
        expected_urls = {
            Organization.PRIVACY_POLICY_URL: "https://some_url.com/privacyPolicyUrl",
            Organization.TERM_AND_CONDITION_URL: "https://some_url.com/termAndConditionUrl",
            Organization.EULA_URL: "https://some_url.com/eulaUrl",
        }
        for field_name, value in expected_urls.items():
            self.assertEqual(value, organization[field_name])

    def test_full_configuration_legal_docs__no_urls_in_org_should_be_generated(self):
        org_id = "5fde855f12db509a2785da06"
        coll_name = MongoOrganizationRepository.ORGANIZATION_COLLECTION
        self.mongo_database[coll_name].update_one(
            {Organization.ID_: ObjectId(org_id)},
            {
                "$set": {
                    Organization.PRIVACY_POLICY_OBJECT: sample_s3_object(),
                    Organization.PRIVACY_POLICY_URL: None,
                    Organization.TERM_AND_CONDITION_OBJECT: sample_s3_object(),
                    Organization.TERM_AND_CONDITION_URL: None,
                    Organization.EULA_OBJECT: sample_s3_object(),
                    Organization.EULA_URL: None,
                }
            },
        )

        headers = self.get_headers_for_token(ORGANIZATION_STAFF_ID)
        rsp = self.flask_client.get(
            self.full_config_path % ORGANIZATION_STAFF_ID, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        organization = rsp.json[ResponseObject.ORGANIZATIONS][0]
        for field_name in legal_docs_url_fields():
            self.assertIsNotNone(organization[field_name])

    def test_retrieve_user_full_configuration_org_staff(self):
        deployment_id_with_localization = "5ed8ae76cf99540b259a7315"
        obs_note_id = "5f15aaea6530a4c3c6db4506"
        headers = self.get_headers_for_token(ORGANIZATION_STAFF_ID)
        rsp = self.flask_client.get(
            self.full_config_path % ORGANIZATION_STAFF_ID, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json[ResponseObject.ORGANIZATIONS]))
        deployments = rsp.json[ResponseObject.DEPLOYMENTS]
        self.assertEqual(3, len(deployments))
        dep = find(
            lambda x: x["deploymentId"] == deployment_id_with_localization, deployments
        )
        obs_note = self.get_observation_note(
            dep[Deployment.MODULE_CONFIGS], obs_note_id
        )
        self.assertEqual("Observation Notes", obs_note[ModuleConfig.MODULE_NAME])

    def test_retrieve_user_full_configuration_deployment_staff(self):
        headers = self.get_headers_for_token(DEPLOYMENT_STAFF_ID)
        rsp = self.flask_client.get(
            self.full_config_path % DEPLOYMENT_STAFF_ID, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, len(rsp.json[ResponseObject.ORGANIZATIONS]))

        deployments = rsp.json[ResponseObject.DEPLOYMENTS]
        self.assertEqual(1, len(deployments))

        note = self.get_observation_note(deployments[0][Deployment.MODULE_CONFIGS])
        self.assertObservationNoteDescriptionEqual(note, "Default localization")

    def test_retrieve_user_full_configuration_deployment_staff_translated_to_user_language(
        self,
    ):
        self.set_user_language(DEPLOYMENT_STAFF_ID, Language.NL)
        headers = self.get_headers_for_token(DEPLOYMENT_STAFF_ID)
        rsp = self.flask_client.get(
            self.full_config_path % DEPLOYMENT_STAFF_ID, headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        deployment = rsp.json[ResponseObject.DEPLOYMENTS][0]
        note = self.get_observation_note(deployment[Deployment.MODULE_CONFIGS])
        self.assertObservationNoteDescriptionEqual(note, "NL localization")

        custom_fields = deployment[Deployment.EXTRA_CUSTOM_FIELDS]
        error_message = custom_fields["phoneNumber"]["errorMessage"]
        self.assertEqual("NL Error localization", error_message)

    def test_failure_upload_personal_documents_by_org_staff(self):
        self.test_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)

        filename = f"user/{USER_1_ID_DEPLOYMENT_X}/PersonalDocuments/"
        with open(TEST_FILE_PATH, "rb") as file:
            data = {
                "filename": filename,
                "mime": "application/octet-stream",
                "file": file,
            }
            rsp = self.flask_client.post(
                f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
                data=data,
                headers=self.get_headers_for_token(ORGANIZATION_STAFF),
                content_type="multipart/form-data",
            )
            self.assertEqual(403, rsp.status_code)

    def test_user_without_role(self):
        headers = self.get_headers_for_token(USER_WITHOUT_ROLE)
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_WITHOUT_ROLE}", headers=headers
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["code"], 100047)

    @staticmethod
    def get_observation_note(array, obs_note_id=None):
        def condition(module_config):
            if obs_note_id:
                return module_config["id"] == obs_note_id
            return module_config["moduleName"] == "Observation Notes"

        return find(condition, array)

    def set_user_language(self, user_id, language):
        self.mongo_database.user.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"language": language}}
        )

    def assertObservationNoteDescriptionEqual(self, note, test_string):
        config_body = note[ModuleConfig.CONFIG_BODY]
        description = config_body["pages"][0]["items"][0]["description"]
        self.assertEqual(test_string, description)

    def test_success_retrieve_user_resources__self_resources(self):
        user_id = "61cb194c630781b664bf8eb5"
        rsp = self.flask_client.get(
            f"{self.base_path}/{user_id}/resources",
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(200, rsp.status_code)
        deployments_key = RetrieveUserResourcesResponseObject.Response.DEPLOYMENTS
        orgs_key = RetrieveUserResourcesResponseObject.Response.ORGANIZATIONS
        expected_resp_keys = [
            orgs_key,
            deployments_key,
        ]
        for key in expected_resp_keys:
            self.assertIn(key, rsp.json)
        self.assertEqual(2, len(rsp.json[deployments_key]))
        self.assertEqual(2, len(rsp.json[orgs_key]))

    def test_failure_retrieve_user_resources__not_own_resources(self):
        user_id = "61cb194c630781b664bf8eb5"
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/resources",
            headers=self.get_headers_for_token(user_id),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_retrieve_user_resources__user_not_allowed(self):
        rsp = self.flask_client.get(
            f"{self.base_path}/{USER_1_ID_DEPLOYMENT_X}/resources",
            headers=self.get_headers_for_token(USER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    def _retrieve_users_with_label_filters(self, label_ids: list[str]):
        payload = {
            RetrieveProfilesRequestObject.FILTERS: {User.LABELS: label_ids},
        }
        rsp = self.flask_client.post(
            f"{self.base_path}/profiles",
            headers={
                **self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X),
            },
            json=payload,
        )
        return rsp

    def _successfully_retrieve_users_with_label_filters(self, label_ids: list[str]):
        rsp = self._retrieve_users_with_label_filters(label_ids)
        self.assertEqual(200, rsp.status_code)
        return rsp
