from io import BytesIO
from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import Role
from extensions.common.s3object import S3Object
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import (
    Deployment,
    ModuleConfig,
    OnboardingModuleConfig,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.models.learn import (
    Learn,
    LearnSection,
    LearnArticle,
    LearnArticleContent,
)
from extensions.deployment.models.status import Status
from extensions.deployment.router.deployment_requests import (
    CloneDeploymentRequestObject,
)
from extensions.key_action.models.key_action_log import KeyAction
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.storage.component import StorageComponent

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
ADMIN_ID = "5e8f0c74b50aa9656c34789b"

SAMPLE_IMAGE = "sample.png"
SAMPLE_VIDEO = "sample.mp4"

LEARN_ID = "5e8eeae1b707216625ca4202"

SECTION_ID = "5e946c69e8002eac4a107f56"
ARTICLE_ID = "5e8c58176207e5f78023e655"

ECONSENT_BASE_URL = f"deployment/{DEPLOYMENT_ID}/econsent/assets"
LEARN_BASE_URL = (
    f"deployment/{DEPLOYMENT_ID}/section/{SECTION_ID}/article/{ARTICLE_ID}/assets"
)

USER_CODE = "53924415"
MANAGER_CODE = "17781957"
PROXY_CODE = "96557443"


class CloneDeploymentTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        StorageComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
    ]

    def setUp(self):
        super().setUp()

        self.headers = self.get_headers_for_token(ADMIN_ID)

        self.base_route = "/api/extensions/v1beta/user/profiles"
        self.deployment_route = "/api/extensions/v1beta"
        self.storage_route = "/api/storage/v1beta"

    def _upload_files(self, deployment_id: str = DEPLOYMENT_ID):
        path = Path(__file__).parent.joinpath(f"fixtures/{SAMPLE_IMAGE}")
        with open(path, "rb") as sample_image:
            image_data = sample_image.read()

        path = Path(__file__).parent.joinpath(f"fixtures/{SAMPLE_VIDEO}")
        with open(path, "rb") as sample_video:
            video_data = sample_video.read()

        # Upload Deployment icon
        data = {
            "filename": f"deployment/{deployment_id}/{SAMPLE_IMAGE}",
            "mime": "application/octet-stream",
            "file": (BytesIO(image_data), "file"),
        }
        rsp = self.flask_client.post(
            f"{self.storage_route}/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(201, rsp.status_code)

        # Upload EConsent files
        data = {
            "filename": f"{ECONSENT_BASE_URL}/{SAMPLE_IMAGE}",
            "mime": "application/octet-stream",
            "file": (BytesIO(video_data), "file"),
        }
        rsp = self.flask_client.post(
            f"{self.storage_route}/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(201, rsp.status_code)

        data = {
            "filename": f"{ECONSENT_BASE_URL}/{SAMPLE_VIDEO}",
            "mime": "application/octet-stream",
            "file": (BytesIO(image_data), "file"),
        }
        rsp = self.flask_client.post(
            f"{self.storage_route}/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(201, rsp.status_code)

        # Upload Learn thumbnail and video
        data = {
            "filename": f"{LEARN_BASE_URL}/{SAMPLE_IMAGE}",
            "mime": "application/octet-stream",
            "file": (BytesIO(image_data), "file"),
        }
        rsp = self.flask_client.post(
            f"{self.storage_route}/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(201, rsp.status_code)

        data = {
            "filename": f"{LEARN_BASE_URL}/{SAMPLE_VIDEO}",
            "mime": "application/octet-stream",
            "file": (BytesIO(video_data), "file"),
        }
        rsp = self.flask_client.post(
            f"{self.storage_route}/upload/{self.config.server.storage.defaultBucket}",
            data=data,
            headers=self.headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(201, rsp.status_code)

    def test_success_clone_deployment(self):
        module_config_id = "5e94b2007773091c9a592650"
        onboarding_config_id = "604c89573a295dad259abb03"
        consent_id = "5e9443789911c97c0b639374"
        econsent_id = "5e9443789911c97c0b639444"
        role_id = "5e8eeae1b707216625ca4203"
        key_action_id = "5f078582c565202bd6cb03af"

        self._upload_files()

        new_name = "New Name"
        body = {
            CloneDeploymentRequestObject.REFERENCE_ID: DEPLOYMENT_ID,
            CloneDeploymentRequestObject.NAME: new_name,
        }
        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/clone", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        deployment_id = rsp.json["id"]

        dep = self.mongo_database["deployment"].find_one(
            {"_id": ObjectId(deployment_id)}
        )
        self.assertEqual(new_name, dep[Deployment.NAME])
        self.assertEqual(Status.DRAFT.name, dep[Deployment.STATUS])
        self.assertEqual(Deployment.FIRST_VERSION, dep[Deployment.VERSION])
        self.assertEqual(
            f"deployment/{deployment_id}/{SAMPLE_IMAGE}",
            dep[Deployment.ICON][S3Object.KEY],
        )

        module_configs = dep[Deployment.MODULE_CONFIGS]
        self.assertEqual(4, len(module_configs))
        self.assertNotEqual(module_config_id, module_configs[0][ModuleConfig.ID])

        onboarding_configs = dep[Deployment.ONBOARDING_CONFIGS]
        self.assertNotEqual(
            onboarding_config_id, onboarding_configs[0][OnboardingModuleConfig.ID]
        )

        # Check Consent
        self.assertNotEqual(consent_id, dep[Deployment.CONSENT][Consent.ID])

        # Check EConsent
        self.assertNotEqual(econsent_id, dep[Deployment.ECONSENT][EConsent.ID])

        new_econsent_base_url = ECONSENT_BASE_URL.replace(DEPLOYMENT_ID, deployment_id)
        consent_sections = dep[Deployment.ECONSENT][EConsent.SECTIONS]
        self.assertEqual(
            f"{new_econsent_base_url}/{SAMPLE_IMAGE}",
            consent_sections[0][EConsentSection.THUMBNAIL_LOCATION][S3Object.KEY],
        )
        self.assertEqual(
            f"{new_econsent_base_url}/{SAMPLE_VIDEO}",
            consent_sections[2][EConsentSection.VIDEO_LOCATION][S3Object.KEY],
        )

        # Check Learn
        sections = dep[Deployment.LEARN][Learn.SECTIONS]
        self.assertNotEqual(LEARN_ID, dep[Deployment.LEARN][Learn.ID])
        self.assertNotEqual(SECTION_ID, sections[0][LearnSection.ID])

        articles = sections[0][LearnSection.ARTICLES]
        self.assertNotEqual(ARTICLE_ID, articles[0][LearnArticle.ID])
        new_learn_url = LEARN_BASE_URL.replace(DEPLOYMENT_ID, deployment_id)

        thumbnail = articles[0][LearnArticle.THUMBNAIL_URL]
        self.assertEqual(f"{new_learn_url}/{SAMPLE_IMAGE}", thumbnail[S3Object.KEY])
        video = articles[0][LearnArticle.CONTENT][LearnArticleContent.VIDEO_URL]
        self.assertEqual(f"{new_learn_url}/{SAMPLE_VIDEO}", video[S3Object.KEY])

        self.assertNotEqual(USER_CODE, dep[Deployment.USER_ACTIVATION_CODE])
        self.assertNotEqual(MANAGER_CODE, dep[Deployment.MANAGER_ACTIVATION_CODE])
        self.assertNotEqual(PROXY_CODE, dep[Deployment.PROXY_ACTIVATION_CODE])
        self.assertNotEqual(role_id, dep[Deployment.ROLES][0][Role.ID])
        self.assertNotEqual(key_action_id, dep[Deployment.KEY_ACTIONS][0][KeyAction.ID])

    def test_success_clone_deployment_without_articles_in_learn(self):
        deployment_id = "612f153c1a297695e4506d53"
        new_name = "New Name for deployment without articles in learn"
        body = {
            CloneDeploymentRequestObject.REFERENCE_ID: deployment_id,
            CloneDeploymentRequestObject.NAME: new_name,
        }
        self._upload_files(deployment_id)
        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/clone", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
