from enum import Enum, auto
from io import BytesIO
from pathlib import Path
from typing import Optional

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.user import User
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveDeploymentConfigResponseObject,
)
from extensions.common.s3object import S3Object
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.module_result.models.primitives.primitive import MeasureUnit
from extensions.module_result.modules import (
    AZScreeningQuestionnaireModule,
    WeightModule,
    HeightModule,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_az_screening,
)
from extensions.tests.shared.test_helpers import consent_log, simple_econsent_log
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

PROXY_USER_ID = "606eba3a2c94383d620b52ad"
REGULAR_USER_ID = "60642e821668fbf7381eefa0"

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"

CONSENT_ID = "5e9443789911c97c0b639374"
E_CONSENT_ID = "5e9443789911c97c0b639444"

DEFAULT_MODULES_PATH = (
    "extensions.authorization.boarding.manager.BoardingManager.default_modules"
)


class Task(Enum):
    AZ_SCREENING = auto()
    CONSENT = auto()
    E_CONSENT = auto()
    ID_VERIFICATION = auto()
    HELPERS_AGREEMENT = auto()
    PREFERRED_UNITS = auto()


tasks_map = {
    Task.AZ_SCREENING: "606705adc7558713d7d398e8",
    Task.CONSENT: "6061cbc41f37f7405c6bb923",
    Task.E_CONSENT: "604c89573a295dad259abb03",
    Task.HELPERS_AGREEMENT: "606ea61c5d52b6ec29d02dac",
    Task.ID_VERIFICATION: "604c895da1adf357ed1fe15f",
    Task.PREFERRED_UNITS: "809efe5df8e24b9f63431811",
}


class OnBoardingManagerTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        StorageComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    override_config = {"server.deployment.enableAuthz": "true"}

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(REGULAR_USER_ID)
        self.base_url = "/api/extensions/v1beta/user"

    def test_success_next_boarding_task_from_user_deployment(self):
        # At first we will use one deployment, then another
        # to make sure boarding manager init each time and not using configs
        # from different deployment

        user_id_from_another_deployment = "5eda5e367adadfb46f7ff71f"
        self.assert_next_on_boarding_task_is(None, user=user_id_from_another_deployment)

        self.assert_next_on_boarding_task_is(Task.CONSENT, user=REGULAR_USER_ID)

    def test_success_proxy_user_full_boarding_path(self):
        self.assert_next_on_boarding_task_is(Task.HELPERS_AGREEMENT, user=PROXY_USER_ID)
        self.submit_helpers_agreement()
        self.assert_next_on_boarding_task_is(Task.CONSENT, user=PROXY_USER_ID)
        self.submit_signature_for(Task.CONSENT, user=PROXY_USER_ID)
        self.assert_next_on_boarding_task_is(None, user=PROXY_USER_ID)

    def test_success_user_full_boarding_path(self):
        self.assert_next_on_boarding_task_is(Task.CONSENT)
        self.assert_can_download_image()
        self.submit_signature_for(Task.CONSENT)

        self.assert_next_on_boarding_task_is(Task.ID_VERIFICATION)
        self.confirm_identity()

        self.assert_next_on_boarding_task_is(Task.AZ_SCREENING)
        self.submit_az_screening_questionnaire()

        self.assert_next_on_boarding_task_is(Task.E_CONSENT)
        self.assert_can_download_image()
        self.submit_signature_for(Task.E_CONSENT)

        self.assert_next_on_boarding_task_is(Task.PREFERRED_UNITS)
        self.submit_preferred_units()

        self.assert_next_on_boarding_task_is(None)

    def test_preferred_units_still_required_after_submitting_not_all_units(self):
        self.set_next_on_boarding_task(Task.PREFERRED_UNITS)

        weight_units = {WeightModule.moduleId: MeasureUnit.KILOGRAM.value}
        self.submit_preferred_units(weight_units)
        self.assert_next_on_boarding_task_is(Task.PREFERRED_UNITS)

    def test_success_when_proxy_user_access_helper_agreement_id_verification_enabled(
        self,
    ):
        onboarding_module_id_verification_id = "604c895da1adf357ed1fe15f"
        self.mongo_database[MongoDeploymentRepository.DEPLOYMENT_COLLECTION].update_one(
            {
                "_id": ObjectId(DEPLOYMENT_ID),
                "onboardingConfigs.id": ObjectId(onboarding_module_id_verification_id),
            },
            {"$set": {"onboardingConfigs.$.userTypes": ["User", "Proxy"]}},
        )

        self.assert_next_on_boarding_task_is(Task.HELPERS_AGREEMENT, user=PROXY_USER_ID)
        self.submit_helpers_agreement()

        self.assert_next_on_boarding_task_is(Task.CONSENT, user=PROXY_USER_ID)

        self.submit_signature_for(Task.CONSENT, user=PROXY_USER_ID)
        self.assert_next_on_boarding_task_is(Task.ID_VERIFICATION, user=PROXY_USER_ID)

    def test_consent_image_not_blocked_before_sign_consent(self):
        self.assert_next_on_boarding_task_is(Task.CONSENT)
        self.assert_can_download_image()
        self.submit_signature_for(Task.CONSENT)

    def test_e_consent_image_not_blocked_before_sign_e_consent(self):
        self.set_next_on_boarding_task(Task.E_CONSENT)
        self.assert_next_on_boarding_task_is(Task.E_CONSENT)
        self.assert_can_download_image()
        self.submit_signature_for(Task.E_CONSENT)

    # helpers
    def get_user_configuration(self, user_id=REGULAR_USER_ID):
        url = f"{self.base_url}/{user_id}/configuration"
        return self.flask_client.get(url, headers=self.get_headers_for_token(user_id))

    def set_next_on_boarding_task(self, task: Task):
        target_id = tasks_map.get(task)
        if not target_id:
            raise NotImplementedError

        collection = MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        self.mongo_database[collection].update_one(
            {
                "_id": ObjectId(DEPLOYMENT_ID),
                "onboardingConfigs.id": ObjectId(target_id),
            },
            {"$set": {"onboardingConfigs.$.order": 1}},
        )

    def upload_file(self, filename: str):
        file_path = Path(__file__).parent.joinpath("fixtures/sample.png")
        with open(file_path, "rb") as file:
            image_data = file.read()

        data = {
            "filename": filename,
            "mime": "application/octet-stream",
            "file": (BytesIO(image_data), "file"),
        }
        return self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.get_headers_for_token(REGULAR_USER_ID),
            content_type="multipart/form-data",
        )

    def assert_can_download_image(self):
        bucket = self.config.server.storage.defaultBucket
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{bucket}/wopps.jpeg",
            headers=self.get_headers_for_token(REGULAR_USER_ID),
        )
        self.assertNotEqual(428, rsp.status_code)

    def assert_next_on_boarding_task_is(
        self, task_name: Optional[Task], user: str = None
    ):
        next_task_key = RetrieveDeploymentConfigResponseObject.NEXT_ONBOARDING_TASK_ID

        rsp = self.get_user_configuration(user or REGULAR_USER_ID)
        if task_name is None:
            self.assertNotIn(next_task_key, rsp.json)
        else:
            expected_task_id = tasks_map.get(task_name)
            task_id = rsp.json[next_task_key]
            self.assertEqual(expected_task_id, task_id, f"Expected {task_name.name}")

    def submit_signature_for(self, task_name: Task, user: str = None):
        user = user or REGULAR_USER_ID
        url = f"{self.base_url}/{user}/%s/%s/sign"
        if task_name == Task.CONSENT:
            log = consent_log()
            url = url % ("consent", CONSENT_ID)
        elif task_name == Task.E_CONSENT:
            log = simple_econsent_log()
            url = url % ("econsent", E_CONSENT_ID)
        else:
            raise NotImplementedError

        signature = {
            S3Object.KEY: f"user/{user}/{task_name.name.lower()}/sample.png",
            S3Object.REGION: "eu",
            S3Object.BUCKET: self.config.server.storage.defaultBucket,
        }
        file_rsp = self.upload_file(signature["key"])
        self.assertEqual(201, file_rsp.status_code)

        log[ConsentLog.SIGNATURE] = signature
        headers = self.get_headers_for_token(user) if user else self.headers
        rsp = self.flask_client.post(url, json=log, headers=headers)
        self.assertEqual(201, rsp.status_code)

    def confirm_identity(self):
        new_status = User.VerificationStatus.ID_VERIFICATION_SUCCEEDED
        self.mongo_database[MongoUserRepository.USER_COLLECTION].update(
            {User.ID_: ObjectId(REGULAR_USER_ID)},
            {"$set": {User.VERIFICATION_STATUS: new_status}},
        )

    def submit_az_screening_questionnaire(self):
        module_result_route = f"{self.base_url}/{REGULAR_USER_ID}/module-result"
        url = f"{module_result_route}/{AZScreeningQuestionnaireModule.moduleId}"
        rsp = self.flask_client.post(
            url, json=[sample_az_screening()], headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

    def submit_preferred_units(self, preferred_units: dict = None):
        units = {
            WeightModule.moduleId: MeasureUnit.KILOGRAM.value,
            HeightModule.moduleId: MeasureUnit.CENTIMETRE.value,
        }
        preferred_units = {User.PREFERRED_UNITS: preferred_units or units}
        rsp = self.flask_client.post(
            f"{self.base_url}/{REGULAR_USER_ID}",
            json=preferred_units,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def submit_helpers_agreement(self):
        url = f"{self.base_url}/{PROXY_USER_ID}/deployment/{DEPLOYMENT_ID}/helperagreementlog"
        new_status = HelperAgreementLog.Status.AGREE_AND_ACCEPT.value
        rsp = self.flask_client.post(
            url,
            json={HelperAgreementLog.STATUS: new_status},
            headers=self.get_headers_for_token(PROXY_USER_ID),
        )
        self.assertEqual(201, rsp.status_code)
