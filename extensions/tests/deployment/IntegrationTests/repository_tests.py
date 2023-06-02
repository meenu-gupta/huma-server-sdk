from bson import ObjectId

from extensions.common.s3object import S3Object
from extensions.common.sort import SortField
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent

from extensions.deployment.models.learn import (
    LearnSection,
    LearnArticle,
    LearnArticleContent,
)
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.exceptions import DeploymentDoesNotExist
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.module_result.models.module_config import ModuleConfig
from extensions.tests.deployment.IntegrationTests.abstract_deployment_test_case_tests import (
    AbstractDeploymentTestCase,
)
from extensions.tests.deployment.IntegrationTests.consent_router_tests import (
    simple_consent,
)
from extensions.tests.deployment.IntegrationTests.learn_routes_tests import (
    simple_article,
)
from extensions.tests.deployment.IntegrationTests.module_config_tests import (
    simple_module_config,
)
from extensions.tests.shared.test_helpers import simple_econsent
from sdk.common.utils import inject

DEPLOYMENT_COLLECTION = "deployment"
VALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
INVALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2d"
DEPLOYMENT_CODE = "AU15"


def test_deployment():
    return {
        Deployment.COLOR: "0x007AFF",
        Deployment.NAME: "Test Deployment",
        Deployment.STATUS: "DRAFT",
        Deployment.CODE: DEPLOYMENT_CODE,
    }


class BaseRepositoryTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.repo = inject.instance(DeploymentRepository)
        self.consent_repo = inject.instance(ConsentRepository)
        self.econsent_repo = inject.instance(EConsentRepository)

    def assertIdCorrect(self, expected, actual):
        self.assertIsInstance(actual, ObjectId)
        self.assertEqual(expected, str(actual))


class DeploymentRepositoryTestCase(BaseRepositoryTestCase):
    def test_create_deployment(self):
        # save new deployment
        deployment = Deployment.from_dict(test_deployment())
        inserted_id = self.repo.create_deployment(deployment)

        # retrieve new deployment by id
        new_deployment = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(inserted_id)}
        )

        # assert userActivationCode is valid
        self.assertIn(Deployment.USER_ACTIVATION_CODE, new_deployment)
        self.assertEqual(8, len(new_deployment[Deployment.USER_ACTIVATION_CODE]))
        self.assertIsInstance(new_deployment[Deployment.USER_ACTIVATION_CODE], str)

        # assert managerActivationCode is valid
        self.assertIn(Deployment.MANAGER_ACTIVATION_CODE, new_deployment)
        self.assertEqual(12, len(new_deployment[Deployment.MANAGER_ACTIVATION_CODE]))
        self.assertIsInstance(new_deployment[Deployment.MANAGER_ACTIVATION_CODE], str)

        # assert userActivationCode is valid
        self.assertIn(Deployment.PROXY_ACTIVATION_CODE, new_deployment)
        self.assertEqual(8, len(new_deployment[Deployment.PROXY_ACTIVATION_CODE]))
        self.assertIsInstance(new_deployment[Deployment.PROXY_ACTIVATION_CODE], str)

        # assert learn was created
        self.assertIn("learn", new_deployment)

        # assert code is valid
        self.assertEqual(new_deployment[Deployment.CODE], DEPLOYMENT_CODE)

    def test_retrieve_deployment(self):
        self.repo.retrieve_deployment(deployment_id=VALID_DEPLOYMENT_ID)

    def test_retrieve_deployment_not_exist(self):
        with self.assertRaises(DeploymentDoesNotExist):
            self.repo.retrieve_deployment(deployment_id=INVALID_DEPLOYMENT_ID)

    def test_retrieve_deployments_no_skip(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=5, name_contains="", sort_fields=[]
        )
        self.assertEqual(5, len(deployments))
        self.assertEqual(8, total)

    def test_retrieve_deployments_skip_five(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=5, limit=0, name_contains="", sort_fields=[]
        )
        self.assertEqual(3, len(deployments))
        self.assertEqual(8, total)

    def test_retrieve_deployments_skip_and_limit(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=5, limit=5, name_contains="", sort_fields=[]
        )
        self.assertEqual(3, len(deployments))
        self.assertEqual(8, total)

    def test_retrieve_deployments_no_skip_no_limit(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=0, name_contains="", sort_fields=[]
        )
        self.assertEqual(8, len(deployments))
        self.assertEqual(8, total)

    def test_retrieve_deployments_with_search(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=0, name_contains="Test", sort_fields=[]
        )
        self.assertEqual(1, len(deployments))
        self.assertEqual(1, total)

    def test_retrieve_deployments_with_search_by_id(self):
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=0, search_criteria="db2c"
        )
        self.assertEqual(1, len(deployments))
        self.assertEqual(1, total)

    def test_retrieve_deployments_sort_by_name_asc(self):
        sort_fields = [SortField.from_dict({"field": "name", "direction": "ASC"})]
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=0, name_contains="", sort_fields=sort_fields
        )
        self.assertEqual(8, len(deployments))
        self.assertEqual(8, total)
        self.assertEqual("Test care plan\\", deployments[0].name)

    def test_retrieve_deployments_sort_by_name_desc(self):
        sort_fields = [SortField.from_dict({"field": "name", "direction": "DESC"})]
        deployments, total = self.repo.retrieve_deployments(
            skip=0, limit=0, name_contains="", sort_fields=sort_fields
        )
        self.assertEqual(8, len(deployments))
        self.assertEqual(8, total)
        self.assertEqual("Test care plan\\", deployments[-1].name)

    def test_update_deployment(self):
        name = "Updated Care Plan"
        deployment = test_deployment()
        deployment["id"] = VALID_DEPLOYMENT_ID
        deployment["name"] = name

        deployment_id = self.repo.update_deployment(Deployment.from_dict(deployment))
        self.assertEqual(deployment["id"], deployment_id)

        updated_deployment = self.repo.retrieve_deployment(
            deployment_id=deployment["id"]
        )
        self.assertEqual(name, updated_deployment.name)

    def test_update_deployment_not_exist(self):
        name = "Updated Care Plan"
        deployment = test_deployment()
        deployment["id"] = INVALID_DEPLOYMENT_ID
        deployment["name"] = name

        with self.assertRaises(DeploymentDoesNotExist):
            self.repo.update_deployment(Deployment.from_dict(deployment))


class LearnRepositoryTestCase(BaseRepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.section_id = "5e946c69e8002eac4a107f56"

    def get_deployment(self, deployment_id: str = None) -> dict:
        return self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(deployment_id)}
        )

    def test_create_learn_section(self):
        learn_section = LearnSection.from_dict(
            {
                "title": "Test section",
                "order": 1,
            }
        )
        inserted_id = self.repo.create_learn_section(
            deployment_id=VALID_DEPLOYMENT_ID, learn_section=learn_section
        )
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        self.assertEqual(inserted_id, str(deployment["learn"]["sections"][-1]["id"]))

    def test_create_learn_article(self):
        learn_article = LearnArticle.from_dict(simple_article())
        inserted_id = self.repo.create_learn_article(
            deployment_id=VALID_DEPLOYMENT_ID,
            section_id=self.section_id,
            learn_article=learn_article,
        )
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        self.assertEqual(
            inserted_id, str(deployment["learn"]["sections"][0]["articles"][-1]["id"])
        )

    def test_update_learn_section(self):
        learn_section = LearnSection.from_dict(
            {
                "id": ObjectId("5e946c69e8002eac4a107f56"),
                "title": "Updated Test section",
                "order": 1,
            }
        )
        learn_section_id = self.repo.update_learn_section(
            deployment_id=VALID_DEPLOYMENT_ID, learn_section=learn_section
        )
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        section = deployment["learn"]["sections"][0]
        self.assertEqual(learn_section_id, str(section["id"]))
        self.assertEqual(learn_section.title, section["title"])

    def test_update_learn_article(self):
        content_object = {
            S3Object.BUCKET: "bucket_name",
            S3Object.KEY: "key_name",
            S3Object.REGION: "us",
        }
        test_article = LearnArticle.from_dict(
            {
                **simple_article(),
                LearnArticle.ID: "5e8c58176207e5f78023e655",
                LearnArticle.TITLE: "Updated Article",
                LearnArticle.CONTENT: {
                    LearnArticleContent.TYPE: "VIDEO",
                    LearnArticleContent.TIME_TO_READ: "20m",
                    LearnArticleContent.TEXT_DETAILS: "Here what you read",
                    LearnArticleContent.CONTENT_OBJECT: content_object,
                },
            }
        )
        learn_section_id = self.repo.update_learn_article(
            deployment_id=VALID_DEPLOYMENT_ID,
            section_id=self.section_id,
            article=test_article,
        )
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        article = deployment["learn"]["sections"][0]["articles"][0]
        self.assertEqual(learn_section_id, str(article["id"]))
        self.assertEqual(test_article.title, article["title"])
        self.assertEqual(
            content_object,
            article[LearnArticle.CONTENT][LearnArticleContent.CONTENT_OBJECT],
        )

    def test_update_learn_article_without_updating_create_date_time(self):
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        article = deployment["learn"]["sections"][0]["articles"][0]
        create_date_time = article[LearnArticle.CREATE_DATE_TIME]
        update_date_time = article[LearnArticle.UPDATE_DATE_TIME]
        test_article = LearnArticle.from_dict(
            {
                **simple_article(),
                "id": "5e8c58176207e5f78023e655",
                "title": "Updated Article",
            }
        )
        learn_section_id = self.repo.update_learn_article(
            deployment_id=VALID_DEPLOYMENT_ID,
            section_id=self.section_id,
            article=test_article,
        )
        deployment = self.get_deployment(VALID_DEPLOYMENT_ID)
        article = deployment["learn"]["sections"][0]["articles"][0]
        self.assertEqual(learn_section_id, str(article["id"]))
        self.assertEqual(create_date_time, article[LearnArticle.CREATE_DATE_TIME])
        self.assertNotEqual(update_date_time, article[LearnArticle.UPDATE_DATE_TIME])


class ConsentRepositoryTestCase(BaseRepositoryTestCase):
    def test_create_consent(self):
        consent_id = self.consent_repo.create_consent(
            deployment_id=VALID_DEPLOYMENT_ID,
            consent=Consent.from_dict(simple_consent()),
        )
        deployment = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(VALID_DEPLOYMENT_ID)}
        )
        new_consent_id = deployment[Deployment.CONSENT][Consent.ID]
        self.assertIdCorrect(consent_id, new_consent_id)


class EConsentRepositoryTestCase(BaseRepositoryTestCase):
    def test_create_econsent(self):
        consent_id = self.econsent_repo.create_econsent(
            deployment_id=VALID_DEPLOYMENT_ID,
            econsent=EConsent.from_dict(simple_econsent()),
        )
        deployment = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(VALID_DEPLOYMENT_ID)}
        )
        new_consent_id = deployment[Deployment.ECONSENT][EConsent.ID]
        self.assertIdCorrect(consent_id, new_consent_id)


class ModuleConfigTestCase(BaseRepositoryTestCase):
    def test_create_module_config(self):
        inserted_id = self.repo.create_module_config(
            deployment_id=VALID_DEPLOYMENT_ID,
            config=ModuleConfig.from_dict(simple_module_config()),
        )
        deployment = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(VALID_DEPLOYMENT_ID)}
        )
        self.assertEqual(inserted_id, str(deployment["moduleConfigs"][-1]["id"]))

    def test_update_module_config_with_new_id(self):
        config_id = "5e94b2007773091c9a592650"

        inserted_id = self.repo.update_module_config(
            deployment_id=VALID_DEPLOYMENT_ID,
            config=ModuleConfig.from_dict(
                {
                    **simple_module_config(),
                    "moduleId": "BloodPressure",
                    "status": "DISABLED",
                    ModuleConfig.ID: config_id,
                }
            ),
        )
        deployment = self.mongo_database[DEPLOYMENT_COLLECTION].find_one(
            {"_id": ObjectId(VALID_DEPLOYMENT_ID)}
        )
        updated_config = deployment[Deployment.MODULE_CONFIGS][0]

        self.assertEqual(ObjectId, type(updated_config[ModuleConfig.ID]))
        self.assertEqual(inserted_id, str(updated_config["id"]))
        self.assertEqual("DISABLED", updated_config["status"])

    def test_success_retrieve_module_config(self):
        module_config_id = "5e94b2007773091c9a592650"
        res = self.repo.retrieve_module_config(module_config_id=module_config_id)
        self.assertEqual(res.id, module_config_id)
