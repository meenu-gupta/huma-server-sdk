from typing import Optional
from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
    VALID_USER_ID,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.auth.component import AuthComponent
from sdk.notification.component import NotificationComponent
from sdk.versioning.component import VersionComponent

VALID_PROXY_ID = "606eba3a2c94383d620b52ad"


class DeploymentOffBoardingTestCase(AbstractDeploymentTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        NotificationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    override_config = {
        **AbstractDeploymentTestCase.override_config,
        "server.deployment.offBoarding": "true",
    }

    base_path = "api/extensions/v1beta/deployment"
    unregister_path = "api/notification/v1beta/device/unregister"

    def setUp(self):
        super(DeploymentOffBoardingTestCase, self).setUp()
        self.remove_onboarding()

    def test_success_access_off_boarding_not_expired(self):
        self.enable_off_boarding("P100Y")
        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(
            f"api/extensions/v1beta/user/{VALID_USER_ID}", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_access_off_boarding_expired(self):
        self.enable_off_boarding()

        self._assert_expected_module_result_status_code(412)
        self._assert_off_boarded(
            VALID_USER_ID, BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        )

        self._assert_expected_module_result_status_code(
            412, self.get_headers_for_token("606eba3a2c94383d620b52ad")
        )
        self._assert_off_boarded(
            VALID_PROXY_ID, BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        )

    def test_permanently_offboarded(self):
        headers = self.get_headers_for_token(VALID_USER_ID)
        self._assert_expected_module_result_status_code(201, headers=headers)
        res = self.get_profile()
        self.assertNotIn(User.BOARDING_STATUS, res)
        self.enable_off_boarding()
        self._assert_expected_module_result_status_code(412, headers=headers)

        self._assert_off_boarded(
            VALID_USER_ID, BoardingStatus.ReasonOffBoarded.USER_COMPLETE_ALL_TASK
        )
        self.disable_off_boarding()
        self._assert_expected_module_result_status_code(412, headers=headers)

    def test_success_access_profile_off_boarding_expired(self):
        self.enable_off_boarding()

        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(
            f"api/extensions/v1beta/user/{VALID_USER_ID}", headers=headers
        )
        self.assertEqual(200, rsp.status_code)

    def test_success_get_config_for_off_boarded_user(self):
        self.enable_off_boarding()

        headers = self.get_headers_for_token(VALID_USER_ID)
        rsp = self.flask_client.get(
            f"api/extensions/v1beta/user/{VALID_USER_ID}/configuration", headers=headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertTrue(rsp.json["isOffBoarded"])

    def test_success_access_unregister_device_route_off_boarding_expired(self):
        self.enable_off_boarding()

        headers = self.get_headers_for_token(VALID_USER_ID)
        json = {"devicePushId": "test_device-push_id"}
        rsp = self.flask_client.delete(self.unregister_path, json=json, headers=headers)
        self.assertEqual(204, rsp.status_code)

    def test_boarding_status_saved_identity_verification(self):
        self.mongo_database["deployment"].update_one(
            {"_id": ObjectId("5d386cc6ff885918d96edb2c")},
            {
                "$set": {
                    "onboardingConfigs": [
                        {
                            "onboardingId": "IdentityVerification",
                            "status": "ENABLED",
                            "order": 3,
                            "version": 1,
                            "configBody": {},
                        }
                    ]
                }
            },
        )

        self.mongo_database[MongoUserRepository.USER_COLLECTION].update_one(
            {User.ID_: ObjectId(VALID_USER_ID)},
            {
                "$set": {
                    User.VERIFICATION_STATUS: User.VerificationStatus.ID_VERIFICATION_FAILED
                }
            },
        )
        self._assert_expected_module_result_status_code(412)
        self._assert_off_boarded(
            VALID_USER_ID, BoardingStatus.ReasonOffBoarded.USER_FAIL_ID_VERIFICATION
        )

    def _assert_off_boarded(self, user_id: str, reason: int):
        res = self.get_profile(user_id)
        boarding_status = res[User.BOARDING_STATUS]
        self.assertIsNotNone(boarding_status)
        self.assertEqual(
            boarding_status[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED
        )
        self.assertEqual(
            boarding_status[BoardingStatus.REASON_OFF_BOARDED],
            reason,
        )

    def get_profile(self, user_id: str = VALID_USER_ID):
        return self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
            {User.ID_: ObjectId(user_id)}
        )

    def enable_off_boarding(self, custom_duration: str = None):
        body = {"features": {"offBoarding": True}, "duration": custom_duration or "P1D"}
        rsp = self.flask_client.put(
            f"{self.base_path}/{self.deployment_id}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

    def disable_off_boarding(self):
        body = {"features": {"offBoarding": False}}
        rsp = self.flask_client.put(
            f"{self.base_path}/{self.deployment_id}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        pass

    def _assert_expected_module_result_status_code(
        self, expected_status_code: int, headers: Optional[dict[str, str]] = None
    ):
        if not headers:
            headers = self.get_headers_for_token(VALID_USER_ID)
        data = {
            **common_fields(),
            "type": "BloodPressure",
            "diastolicValue": 80,
            "systolicValue": 80,
        }
        rsp = self.flask_client.post(
            f"api/extensions/v1beta/user/{VALID_USER_ID}/module-result/BloodPressure",
            headers=headers,
            json=[data],
        )
        self.assertEqual(expected_status_code, rsp.status_code)
