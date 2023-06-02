import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId
from freezegun import freeze_time
from freezegun.api import FakeDatetime
from pymongo import MongoClient

from extensions.deployment.exceptions import (
    DeploymentDoesNotExist,
    DeploymentWithVersionNumberDoesNotExist,
)
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
    CarePlanGroup,
)
from extensions.deployment.models.deployment import (
    Deployment,
    DeploymentRevision,
    Label,
    OnboardingModuleConfig,
    DeploymentTemplate,
)
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    Learn,
    LearnSection,
    LearnArticle,
    OrderUpdateObject,
)
from extensions.deployment.repository.mongo_deployment_repository import (
    MongoDeploymentRepository,
)
from extensions.exceptions import LearnSectionDoesNotExist
from extensions.module_result.models.module_config import ModuleConfig
from sdk import convertibleclass
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from pymongo.database import Database

from sdk.common.utils.convertible import ConvertibleClassValidationError

REPO_PATH = "extensions.deployment.repository.mongo_deployment_repository"
INJECT_PATH = f"{REPO_PATH}.inject"
GENERATE_CODE_PATH = f"{REPO_PATH}.generate_code"
SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"
COLLECTION = MongoDeploymentRepository.DEPLOYMENT_COLLECTION


class MockPhoenixServerConfig:
    instance = MagicMock()


@convertibleclass
class MockDummyDeploymentAttribute:
    instance = MagicMock()


class MockMongoClient:
    class MockSession:
        start_transaction = MagicMock(return_value="")
        commit_transaction = MagicMock(return_value="")
        end_session = MagicMock()

    start_session = MagicMock(return_value=MockSession())


class MongoDeploymentRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

        def bind_and_configure(binder):
            binder.bind(Database, self.db)
            binder.bind(MongoClient, MockMongoClient)

        inject.clear_and_configure(bind_and_configure)

    def tearDown(self) -> None:
        MockMongoClient.start_session().end_session.reset_mock()
        MockMongoClient.start_session().start_transaction.reset_mock()
        MockMongoClient.start_session.reset_mock()

    @patch(INJECT_PATH, MagicMock())
    @patch(GENERATE_CODE_PATH)
    def test_success_generate_manager_code(self, gen_code):
        gen_code.return_value = 111
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        db[COLLECTION].count_documents.return_value = 0
        repo.generate_manager_code()
        db[COLLECTION].count_documents.assert_called_with(
            {"$or": [{"userActivationCode": 111}, {"managerActivationCode": 111}]}
        )

    @patch(INJECT_PATH, MagicMock())
    @patch(GENERATE_CODE_PATH)
    def test_success_generate_user_code(self, gen_code):
        gen_code.return_value = 111
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        db[COLLECTION].count_documents.return_value = 0
        repo.generate_user_code()
        db[COLLECTION].count_documents.assert_called_with(
            {"$or": [{"userActivationCode": 111}, {"managerActivationCode": 111}]}
        )

    @patch(INJECT_PATH, MagicMock())
    @patch(GENERATE_CODE_PATH)
    def test_success_generate_proxy_code(self, gen_code):
        gen_code.return_value = 111
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        db[COLLECTION].count_documents.return_value = 0
        repo.generate_proxy_code()
        db[COLLECTION].count_documents.assert_called_with(
            {"$or": [{"userActivationCode": 111}, {"managerActivationCode": 111}]}
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_localization(self):
        repo = MongoDeploymentRepository()
        deployment_id = SAMPLE_VALID_OBJ_ID
        locale = Language.EN
        repo.retrieve_localization(deployment_id=deployment_id, locale=locale)
        self.db[COLLECTION].find_one.assert_called_with(
            {Deployment.ID_: ObjectId(SAMPLE_VALID_OBJ_ID)}
        )

        self.db[COLLECTION].find_one = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.retrieve_localization(deployment_id=deployment_id, locale=locale)

    @freeze_time("2012-01-01")
    @patch(INJECT_PATH, MagicMock())
    def test_success_update_localizations(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        localizations = {"a": "b"}
        repo.update_localizations(
            deployment_id=deployment_id, localizations=localizations
        )
        db[COLLECTION].find_one_and_update.assert_called_with(
            {Deployment.ID_: ObjectId(SAMPLE_VALID_OBJ_ID)},
            {
                "$set": {
                    Deployment.LOCALIZATIONS: {"a": "b"},
                    Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                }
            },
            session=None,
        )

        db[COLLECTION].find_one_and_update = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.update_localizations(
                deployment_id=deployment_id, localizations=localizations
            )

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_user_notes(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        user_id = SAMPLE_VALID_OBJ_ID
        repo.retrieve_user_notes(deployment_id=deployment_id, user_id=user_id)
        collection = MongoDeploymentRepository.CARE_PLAN_GROUP_LOG_COLLECTION
        db.get_collection(collection).find.assert_called_with(
            {
                CarePlanGroupLog.USER_ID: ObjectId(user_id),
                CarePlanGroupLog.DEPLOYMENT_ID: ObjectId(deployment_id),
            }
        )

        db.get_collection(collection).find = MagicMock(
            return_value=[{"_id": SAMPLE_VALID_OBJ_ID}]
        )
        repo.retrieve_user_notes(deployment_id=deployment_id, user_id=user_id)

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_user_care_plan_group_log(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        user_id = SAMPLE_VALID_OBJ_ID
        repo.retrieve_user_care_plan_group_log(
            deployment_id=deployment_id, user_id=user_id
        )
        collection = MongoDeploymentRepository.CARE_PLAN_GROUP_LOG_COLLECTION
        db.get_collection(collection).find.assert_called_with(
            {
                CarePlanGroupLog.USER_ID: ObjectId(user_id),
                CarePlanGroupLog.DEPLOYMENT_ID: ObjectId(deployment_id),
            }
        )

        db.get_collection(collection).find = MagicMock(
            return_value=[{"_id": SAMPLE_VALID_OBJ_ID}]
        )
        repo.retrieve_user_care_plan_group_log(
            deployment_id=deployment_id, user_id=user_id
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_create_or_update_roles(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        repo.create_or_update_roles(deployment_id=deployment_id, roles=[])
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {"$set": {Deployment.ROLES: []}},
            session=None,
        )

        class MockResult:
            matched_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockResult)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_or_update_roles(deployment_id=deployment_id, roles=[])

    @patch(INJECT_PATH, MagicMock())
    def test_success_create_care_plan_group(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        care_plan_group = CarePlanGroup.from_dict({})
        repo.create_care_plan_group(
            deployment_id=deployment_id, care_plan_group=care_plan_group
        )
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {"$set": {Deployment.CARE_PLAN_GROUP: {}}},
            session=None,
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_delete_key_action(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        key_action_id = SAMPLE_VALID_OBJ_ID
        repo.delete_key_action(deployment_id=deployment_id, key_action_id=key_action_id)
        db.get_collection(COLLECTION).update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$pull": {
                    Deployment.KEY_ACTIONS: {
                        KeyActionConfig.ID: ObjectId(key_action_id)
                    }
                }
            },
            session=None,
        )

        class MockUpdateResult(MagicMock):
            matched_count = 0

        mock_result = MockUpdateResult()
        db.get_collection(COLLECTION).update_one = MagicMock(return_value=mock_result)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.delete_key_action(
                deployment_id=deployment_id, key_action_id=key_action_id
            )

        mock_result.matched_count = 1
        mock_result.modified_count = 0
        db.get_collection(COLLECTION).update_one = MagicMock(return_value=mock_result)
        with self.assertRaises(ObjectDoesNotExist):
            repo.delete_key_action(
                deployment_id=deployment_id, key_action_id=key_action_id
            )

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    def test_success_delete_learn_article(self):
        deployment_id = SAMPLE_VALID_OBJ_ID
        section_id = SAMPLE_VALID_OBJ_ID
        article_id = SAMPLE_VALID_OBJ_ID
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        repo.delete_learn_article(
            deployment_id=deployment_id, section_id=section_id, article_id=article_id
        )
        pull_key = f"{Deployment.LEARN}.{Learn.SECTIONS}.$.{LearnSection.ARTICLES}"
        db[COLLECTION].update_one.assert_called_with(
            {
                Deployment.ID_: ObjectId(deployment_id),
                f"{Deployment.LEARN}.{Learn.SECTION_ID}": ObjectId(section_id),
            },
            {
                "$pull": {pull_key: {"id": ObjectId(article_id)}},
                "$set": {Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0)},
            },
            session=None,
        )

        class MockResult:
            modified_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockResult)
        with self.assertRaises(ObjectDoesNotExist):
            repo.delete_learn_article(
                deployment_id=deployment_id,
                section_id=section_id,
                article_id=article_id,
            )

    @freeze_time("2012-01-01")
    @patch(INJECT_PATH, MagicMock())
    def test_success_delete_learn_section(self):
        deployment_id = SAMPLE_VALID_OBJ_ID
        section_id = SAMPLE_VALID_OBJ_ID
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        repo.delete_learn_section(deployment_id=deployment_id, section_id=section_id)
        pull_key = f"{Deployment.LEARN}.{Learn.SECTIONS}"
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$pull": {pull_key: {LearnSection.ID: ObjectId(section_id)}},
                "$set": {Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0)},
            },
            session=None,
        )

        class MockResult:
            modified_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockResult)
        with self.assertRaises(ObjectDoesNotExist):
            repo.delete_learn_section(
                deployment_id=deployment_id, section_id=section_id
            )

    @patch(INJECT_PATH, MagicMock())
    @patch("extensions.deployment.repository.mongo_deployment_repository.ObjectId")
    def test_success_delete_deployment(self, obj_id_mock):
        deployment_id = SAMPLE_VALID_OBJ_ID
        obj_id_mock.return_value = "111"
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        repo.delete_deployment(deployment_id=deployment_id)
        db[COLLECTION].find_one_and_delete.assert_called_with(
            {Deployment.ID_: "111"}, session=None
        )

    @freeze_time("2012-01-01")
    @patch(INJECT_PATH, MagicMock())
    def test_success_update_key_action(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        key_action_id = SAMPLE_VALID_OBJ_ID
        key_action_dict = {
            KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "P6M",
            KeyActionConfig.DURATION_ISO: "P6M",
            KeyActionConfig.TYPE: KeyActionConfig.Type.LEARN.value,
            KeyActionConfig.TRIGGER: KeyActionConfig.Trigger.SIGN_UP.value,
            KeyActionConfig.ID: ObjectId(SAMPLE_VALID_OBJ_ID),
        }
        key_action = KeyActionConfig.from_dict(key_action_dict)
        deployment_dict = {
            Deployment.NAME: "Test deployment",
            Deployment.KEY_ACTIONS: [key_action_dict],
        }
        db[
            MongoDeploymentRepository.DEPLOYMENT_COLLECTION
        ].find_one.return_value = deployment_dict
        repo.update_key_action(
            deployment_id=deployment_id,
            key_action_id=key_action_id,
            key_action=key_action,
        )
        db[COLLECTION].update_one.assert_called_with(
            {
                Deployment.ID_: ObjectId(deployment_id),
                f"{Deployment.KEY_ACTIONS}.id": ObjectId(key_action_id),
            },
            {
                "$set": {
                    f"{Deployment.KEY_ACTIONS}.$[elem]": key_action_dict,
                    Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                }
            },
            array_filters=[{"elem.id": {"$eq": ObjectId(key_action_id)}}],
            session=None,
        )

        db[COLLECTION].find_one = MagicMock(return_value=None)
        with self.assertRaises(ObjectDoesNotExist):
            repo.update_key_action(
                deployment_id=deployment_id,
                key_action_id=key_action_id,
                key_action=key_action,
            )
            db[COLLECTION].update_one.assert_not_called()

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_deployment(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        repo.retrieve_deployment(deployment_id=deployment_id)
        db[COLLECTION].find_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)}
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_deployment_codes(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_ids = [SAMPLE_VALID_OBJ_ID]
        repo.retrieve_deployment_codes(deployment_ids)
        db[COLLECTION].find.assert_called_with(
            {"_id": {"$in": [ObjectId(SAMPLE_VALID_OBJ_ID)]}}, {"code": 1}
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_deployments_by_ids(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_ids = [SAMPLE_VALID_OBJ_ID, "*"]
        repo.retrieve_deployments_by_ids(deployment_ids)
        db[COLLECTION].find.assert_called_with(
            {"_id": {"$in": [ObjectId(SAMPLE_VALID_OBJ_ID)]}}
        )

    @patch(INJECT_PATH, MagicMock())
    def test_success_retrieve_deployments(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        repo.retrieve_deployments()
        db[COLLECTION].aggregate.assert_called_once()

        db[COLLECTION].aggregate = MagicMock(
            return_value=iter(
                [{"results": [{"_id": SAMPLE_VALID_OBJ_ID}], "totalCount": 0}]
            )
        )
        repo.retrieve_deployments()

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    @patch("extensions.deployment.repository.mongo_deployment_repository.ObjectId")
    def test_success_create_learn_section(self, obj_id_mock):
        db = MagicMock()
        obj_id_mock.return_value = SAMPLE_VALID_OBJ_ID
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        learn_section = LearnSection.from_dict({})
        repo.create_learn_section(
            deployment_id=deployment_id, learn_section=learn_section
        )
        db[COLLECTION].update_one.assert_called_with(
            {"_id": ObjectId(SAMPLE_VALID_OBJ_ID)},
            {
                "$push": {
                    "learn.sections": {
                        LearnSection.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                        LearnSection.CREATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                        LearnSection.ID: SAMPLE_VALID_OBJ_ID,
                    }
                },
                "$set": {Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0)},
            },
            session=None,
        )

        class MockUpdateResult:
            modified_count = 0

        db[repo.DEPLOYMENT_COLLECTION].update_one = MagicMock(
            return_value=MockUpdateResult
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_learn_section(
                deployment_id=deployment_id, learn_section=learn_section
            )

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    @patch("extensions.deployment.repository.mongo_deployment_repository.ObjectId")
    def test_success_create_key_action(self, obj_id_mock):
        db = MagicMock()
        obj_id_mock.return_value = SAMPLE_VALID_OBJ_ID
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID

        key_action = KeyActionConfig.from_dict(
            {
                KeyActionConfig.DELTA_FROM_TRIGGER_TIME: "P6M",
                KeyActionConfig.DURATION_ISO: "P6M",
                KeyActionConfig.TYPE: KeyActionConfig.Type.LEARN.value,
                KeyActionConfig.TRIGGER: KeyActionConfig.Trigger.SIGN_UP.value,
                KeyActionConfig.ID: ObjectId(SAMPLE_VALID_OBJ_ID),
            }
        )
        repo.create_key_action(deployment_id=deployment_id, key_action=key_action)
        key_action_dict = key_action.to_dict(
            include_none=False,
            ignored_fields=repo.IGNORED_FIELDS,
        )
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$push": {Deployment.KEY_ACTIONS: key_action_dict},
                "$set": {Deployment.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0)},
            },
            upsert=True,
            session=None,
        )

        class MockUpdateResult:
            matched_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockUpdateResult)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_key_action(deployment_id=deployment_id, key_action=key_action)

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    @patch("extensions.deployment.repository.mongo_deployment_repository.ObjectId")
    def test_success_create_label(self, obj_id_mock):
        db = MagicMock()
        obj_id_mock.return_value = SAMPLE_VALID_OBJ_ID
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID

        label = Label.from_dict(
            {
                Label.AUTHOR_ID: ObjectId(SAMPLE_VALID_OBJ_ID),
                Label.TEXT: "RECOVERED",
                Label.ID: ObjectId(SAMPLE_VALID_OBJ_ID),
            }
        )
        repo.create_deployment_labels(deployment_id=deployment_id, labels=[label])
        label_dict = [
            label.to_dict(
                include_none=False,
            )
        ]
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$push": {f"{Deployment.LABELS}": {"$each": label_dict}},
            },
            session=None,
        )

        class MockUpdateResult:
            matched_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockUpdateResult)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_deployment_labels(deployment_id=deployment_id, labels=[label])

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    @patch("extensions.deployment.repository.mongo_deployment_repository.ObjectId")
    def test_success_update_labels(self, obj_id_mock):
        db = MagicMock()
        obj_id_mock.return_value = SAMPLE_VALID_OBJ_ID
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID

        label = Label.from_dict(
            {
                Label.AUTHOR_ID: SAMPLE_VALID_OBJ_ID,
                Label.TEXT: "RECOVERED",
                Label.UPDATE_DATE_TIME: FakeDatetime(2012, 1, 1, 0, 0),
                Label.UPDATED_BY: SAMPLE_VALID_OBJ_ID,
                Label.ID: ObjectId(SAMPLE_VALID_OBJ_ID),
            }
        )
        repo.update_deployment_labels(
            deployment_id=deployment_id, labels=[label], updated_label=label
        )
        label_dict = label.to_dict(
            include_none=False,
        )
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {
                "$set": {f"{Deployment.LABELS}": [label_dict]},
            },
            session=None,
        )

        class MockUpdateResult:
            matched_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockUpdateResult)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.update_deployment_labels(
                deployment_id=deployment_id, labels=[label], updated_label=label
            )

    @patch(INJECT_PATH, MagicMock())
    @freeze_time("2012-01-01")
    def test_success_delete_label(self):
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id = SAMPLE_VALID_OBJ_ID
        label_id = SAMPLE_VALID_OBJ_ID

        repo.delete_deployment_label(deployment_id=deployment_id, label_id=label_id)
        db[COLLECTION].update_one.assert_called_with(
            {Deployment.ID_: ObjectId(deployment_id)},
            {"$pull": {f"{Deployment.LABELS}": {Label.ID: ObjectId(label_id)}}},
            session=None,
        )

        class MockUpdateResult:
            matched_count = 1
            modified_count = 0

        db[COLLECTION].update_one = MagicMock(return_value=MockUpdateResult)
        with self.assertRaises(ObjectDoesNotExist):
            repo.delete_deployment_label(deployment_id=deployment_id, label_id=label_id)

    def test_failure_update_deployment_with_unacceptable_fields(self):
        repo = MongoDeploymentRepository()
        unacceptable_fields = [
            Deployment.KEY_ACTIONS,
            Deployment.LEARN,
            Deployment.CONSENT,
            Deployment.ECONSENT,
            Deployment.MODULE_CONFIGS,
            Deployment.ONBOARDING_CONFIGS,
            Deployment.USER_ACTIVATION_CODE,
            Deployment.MANAGER_ACTIVATION_CODE,
            Deployment.ENROLLMENT_COUNTER,
            Deployment.ROLES,
        ]
        for field in unacceptable_fields:
            deployment = Deployment()
            deployment.__setattr__(field, MockDummyDeploymentAttribute())
            with self.assertRaises(ConvertibleClassValidationError):
                repo.update_deployment(deployment=deployment)

    @patch(INJECT_PATH, MagicMock())
    @patch(GENERATE_CODE_PATH)
    def test_retrieve_deployment_revision_called_with_object_id(self, gen_code):
        gen_code.return_value = 111
        db = MagicMock()
        repo = MongoDeploymentRepository(database=db)
        deployment_id_as_obj_id = ObjectId()
        repo.retrieve_deployment_revisions(deployment_id=str(deployment_id_as_obj_id))
        expected_query = {DeploymentRevision.DEPLOYMENT_ID: deployment_id_as_obj_id}
        db[COLLECTION].find.assert_called_once_with(expected_query)

    @patch(f"{REPO_PATH}.MongoDeploymentTemplateModel")
    def test_retrieve_deployment_templates__org_is_passed(self, model):
        org_id = str(ObjectId())
        repo = MongoDeploymentRepository()
        repo.retrieve_deployment_templates(org_id)
        model.objects.assert_called_with(organizationIds=org_id)

    @patch(f"{REPO_PATH}.MongoDeploymentTemplateModel")
    def test_retrieve_deployment_templates(self, model):
        repo = MongoDeploymentRepository()
        repo.retrieve_deployment_templates()
        model.objects.assert_called_once()

    @patch(f"{REPO_PATH}.MongoDeploymentTemplateModel")
    @patch(f"{REPO_PATH}.DeploymentTemplate", MagicMock())
    def test_retrieve_deployment_template(self, model):
        template_id = str(ObjectId())
        repo = MongoDeploymentRepository()
        repo.retrieve_deployment_template(template_id)
        model.objects.assert_called_with(id=template_id)

        model.objects().first = MagicMock(return_value=None)
        with self.assertRaises(ObjectDoesNotExist):
            repo.retrieve_deployment_template(template_id)

    def test_start_transaction(self):
        repo = MongoDeploymentRepository()
        repo.start_transaction()
        MockMongoClient.start_session.assert_called_once()
        MockMongoClient.start_session().start_transaction.assert_called_once()

    def test_commit_transactions(self):
        repo = MongoDeploymentRepository()
        repo.start_transaction()
        repo.commit_transactions()
        MockMongoClient.start_session().commit_transaction.assert_called_once()
        MockMongoClient.start_session().end_session.assert_called_once()
        self.assertIsNone(repo.session)

    def test_create_deployment_revision(self):
        repo = MongoDeploymentRepository()
        dep_revision = DeploymentRevision()
        repo.create_deployment_revision(dep_revision)

        class MockResult:
            inserted_id = ""

        self.db[repo.DEPLOYMENT_COLLECTION].insert_one = MagicMock(
            return_value=MockResult()
        )

    def test_create_onboarding_module_config(self):
        repo = MongoDeploymentRepository()
        config = OnboardingModuleConfig.from_dict(
            {
                "onboardingId": "IdentityVerification",
                "status": "ENABLED",
                "id": "604c895da1adf357ed1fe15f",
                "order": 2,
                "version": 1,
                "userTypes": ["User"],
                "configBody": {
                    "requiredReports": ["DOCUMENT", "FACIAL_SIMILARITY_PHOTO"]
                },
            }
        )
        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_onboarding_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID, config=config
            )

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=MagicMock()
        )
        try:
            repo.create_onboarding_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID, config=config
            )
        except DeploymentDoesNotExist:
            self.fail()

    def test_create_module_config(self):
        repo = MongoDeploymentRepository()
        config = ModuleConfig(id=SAMPLE_VALID_OBJ_ID, moduleId="module id", version=0)

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_module_config(deployment_id=SAMPLE_VALID_OBJ_ID, config=config)

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=MagicMock()
        )
        try:
            repo.create_module_config(deployment_id=SAMPLE_VALID_OBJ_ID, config=config)
        except DeploymentDoesNotExist:
            self.fail()

    def test_update_module_config(self):
        repo = MongoDeploymentRepository()
        config = ModuleConfig(id=SAMPLE_VALID_OBJ_ID, moduleId="module id", version=0)
        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock()
        try:
            repo.update_module_config(deployment_id=SAMPLE_VALID_OBJ_ID, config=config)
        except Exception as error:
            self.fail(error)

    def test_create_key_action(self):
        repo = MongoDeploymentRepository()
        config = KeyActionConfig(id="key_action_test1", learnArticleId="article_test1")

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MagicMock()
        try:
            repo.create_key_action(deployment_id=SAMPLE_VALID_OBJ_ID, key_action=config)
        except DeploymentDoesNotExist:
            self.fail()

    def test_create_learn_article(self):
        repo = MongoDeploymentRepository()
        section_id = "session id"
        learn_article = LearnArticle(id="article_test1", title="article_test1")

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MagicMock()
        try:
            repo.create_learn_article(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                section_id=section_id,
                learn_article=learn_article,
            )
        except DeploymentDoesNotExist:
            self.fail()

        class MockUpdateResult(MagicMock):
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MockUpdateResult()
        with self.assertRaises(DeploymentDoesNotExist):
            repo.create_learn_article(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                section_id=section_id,
                learn_article=learn_article,
            )

    def test_retrieve_deployment_document(self):
        repo = MongoDeploymentRepository()
        repo.retrieve_deployment_document(deployment_id=SAMPLE_VALID_OBJ_ID)
        self.db[repo.DEPLOYMENT_COLLECTION].find_one.assert_called_once()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.retrieve_deployment_document(deployment_id=SAMPLE_VALID_OBJ_ID)

    def test_retrieve_deployment_by_version_number(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(
            return_value={"_id": SAMPLE_VALID_OBJ_ID}
        )
        repo.retrieve_deployment_by_version_number(
            deployment_id=SAMPLE_VALID_OBJ_ID, version_number=1
        )

        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        self.db[repo.DEPLOYMENT_REVISION_COLLECTION].find_one = MagicMock(
            return_value={"_id": SAMPLE_VALID_OBJ_ID}
        )
        try:
            repo.retrieve_deployment_by_version_number(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                version_number=Deployment.FIRST_VERSION,
            )
        except DeploymentWithVersionNumberDoesNotExist:
            self.fail()

        self.db[repo.DEPLOYMENT_REVISION_COLLECTION].find_one = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentWithVersionNumberDoesNotExist):
            repo.retrieve_deployment_by_version_number(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                version_number=Deployment.FIRST_VERSION,
            )

        self.db[repo.DEPLOYMENT_REVISION_COLLECTION].find_one = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentWithVersionNumberDoesNotExist):
            repo.retrieve_deployment_by_version_number(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                version_number=Deployment.FIRST_VERSION + 1,
            )

    def test_retrieve_deployment_by_activation_code(self):
        repo = MongoDeploymentRepository()
        repo.retrieve_deployment_by_activation_code("")
        self.db[repo.DEPLOYMENT_COLLECTION].find_one.assert_called_once()

        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.retrieve_deployment_by_activation_code("")

    def test_retrieve_module_configs(self):
        repo = MongoDeploymentRepository()
        repo.retrieve_module_configs(deployment_id=SAMPLE_VALID_OBJ_ID)
        self.db.get_collection.assert_called_once()

        self.db.get_collection().find_one = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.retrieve_module_configs(deployment_id=SAMPLE_VALID_OBJ_ID)

    def test_check_field_value_exists_in_module_configs(self):
        repo = MongoDeploymentRepository()
        repo.check_field_value_exists_in_module_configs("", "")
        self.db[repo.DEPLOYMENT_COLLECTION].find_one.assert_called_once()

    def test_retrieve_onboarding_module_configs(self):
        repo = MongoDeploymentRepository()
        repo.retrieve_onboarding_module_configs(deployment_id=SAMPLE_VALID_OBJ_ID)

        self.db.get_collection.assert_called_once()

        self.db.get_collection().find_one = MagicMock(return_value=None)
        with self.assertRaises(DeploymentDoesNotExist):
            repo.retrieve_onboarding_module_configs(deployment_id=SAMPLE_VALID_OBJ_ID)

    def test_retrieve_article_by_id(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(
            return_value={
                "_id": SAMPLE_VALID_OBJ_ID,
                "learn": {"id": SAMPLE_VALID_OBJ_ID},
            }
        )
        with self.assertRaises(ObjectDoesNotExist):
            repo.retrieve_article_by_id("", "")

        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(
            return_value={
                "_id": SAMPLE_VALID_OBJ_ID,
                "learn": {
                    "id": "5e8eeae1b707216625ca4202",
                    "sections": [
                        {
                            "id": "5e946c69e8002eac4a107f56",
                            "articles": [
                                {
                                    "id": "5e8c58176207e5f78023e655",
                                }
                            ],
                        }
                    ],
                },
            }
        )
        try:
            repo.retrieve_article_by_id(
                "5e8c58176207e5f78023e655", "5e8c58176207e5f78023e655"
            )
        except ObjectDoesNotExist:
            self.fail()

    def test_retrieve_module_config(self):
        repo = MongoDeploymentRepository()
        self.db.get_collection().find_one = MagicMock(return_value=None)
        repo.retrieve_module_config(module_config_id=SAMPLE_VALID_OBJ_ID)

    def test_retrieve_key_actions(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        repo.retrieve_key_actions(deployment_id=SAMPLE_VALID_OBJ_ID)

    def test_update_enrollment_counter(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock()
        try:
            repo.update_enrollment_counter(deployment_id=SAMPLE_VALID_OBJ_ID)
        except DeploymentDoesNotExist:
            self.fail()

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.update_enrollment_counter(deployment_id=SAMPLE_VALID_OBJ_ID)

    def test_update_learn_section(self):
        repo = MongoDeploymentRepository()
        learn_section = LearnSection(
            id=SAMPLE_VALID_OBJ_ID,
            articles=[LearnArticle(id="articleId2")],
            title="some_section_title",
        )
        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MagicMock()
        repo.update_learn_section(
            deployment_id=SAMPLE_VALID_OBJ_ID, learn_section=learn_section
        )

        class MockUpdateResult:
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MagicMock(
            return_value=MockUpdateResult
        )
        with self.assertRaises(LearnSectionDoesNotExist):
            repo.update_learn_section(
                deployment_id=SAMPLE_VALID_OBJ_ID, learn_section=learn_section
            )

    def test_update_key_action(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        config = KeyActionConfig(id="key_action_test1", learnArticleId="article_test1")
        with self.assertRaises(ObjectDoesNotExist):
            repo.update_key_action(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                key_action_id=SAMPLE_VALID_OBJ_ID,
                key_action=config,
            )

    def test_delete_module_config(self):
        repo = MongoDeploymentRepository()
        try:
            repo.delete_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID, module_config_id=SAMPLE_VALID_OBJ_ID
            )
        except DeploymentDoesNotExist:
            self.fail()

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.delete_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID, module_config_id=SAMPLE_VALID_OBJ_ID
            )

    def test_delete_onboarding_module_config(self):
        repo = MongoDeploymentRepository()
        try:
            repo.delete_onboarding_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                onboarding_config_id=SAMPLE_VALID_OBJ_ID,
            )
            self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update.assert_called_once()
        except DeploymentDoesNotExist:
            self.fail()

        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo.delete_onboarding_module_config(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                onboarding_config_id=SAMPLE_VALID_OBJ_ID,
            )

    def test_reorder_learn_sections(self):
        repo = MongoDeploymentRepository()
        repo.reorder_learn_sections(deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[])

        order_data = OrderUpdateObject.from_dict(
            {OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID, OrderUpdateObject.ORDER: 1}
        )

        class MockResult(MagicMock):
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MockResult

        with self.assertRaises(ObjectDoesNotExist):
            repo.reorder_learn_sections(
                deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[order_data]
            )

    def test_reorder_learn_articles(self):
        repo = MongoDeploymentRepository()
        repo.reorder_learn_articles(
            deployment_id=SAMPLE_VALID_OBJ_ID,
            section_id=SAMPLE_VALID_OBJ_ID,
            ordering_data=[],
        )
        order_data = OrderUpdateObject.from_dict(
            {OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID, OrderUpdateObject.ORDER: 1}
        )

        class MockResult(MagicMock):
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MockResult
        with self.assertRaises(ObjectDoesNotExist):
            repo.reorder_learn_articles(
                deployment_id=SAMPLE_VALID_OBJ_ID,
                section_id=SAMPLE_VALID_OBJ_ID,
                ordering_data=[order_data],
            )

    def test_reorder_onboarding_module_configs(self):
        repo = MongoDeploymentRepository()
        repo.reorder_onboarding_module_configs(
            deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[]
        )
        order_data = OrderUpdateObject.from_dict(
            {OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID, OrderUpdateObject.ORDER: 1}
        )

        class MockResult(MagicMock):
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MockResult
        with self.assertRaises(ObjectDoesNotExist):
            repo.reorder_onboarding_module_configs(
                deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[order_data]
            )

    def test_reorder_module_configs(self):
        repo = MongoDeploymentRepository()
        repo.reorder_module_configs(deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[])
        order_data = OrderUpdateObject.from_dict(
            {OrderUpdateObject.ID: SAMPLE_VALID_OBJ_ID, OrderUpdateObject.ORDER: 1}
        )

        class MockResult(MagicMock):
            modified_count = 0

        self.db[repo.DEPLOYMENT_COLLECTION].update_one = MockResult
        with self.assertRaises(ObjectDoesNotExist):
            repo.reorder_module_configs(
                deployment_id=SAMPLE_VALID_OBJ_ID, ordering_data=[order_data]
            )

    def test_retrieve_deployment_revision_by_module_config_version(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(return_value=None)
        repo.retrieve_deployment_revision_by_module_config_version(
            SAMPLE_VALID_OBJ_ID, SAMPLE_VALID_OBJ_ID, 1
        )

        self.db[repo.DEPLOYMENT_COLLECTION].find_one = MagicMock(
            return_value={"_id": SAMPLE_VALID_OBJ_ID}
        )
        repo.retrieve_deployment_revision_by_module_config_version(
            SAMPLE_VALID_OBJ_ID, SAMPLE_VALID_OBJ_ID, 1
        )

    def test_create_deployment_template(self):
        repo = MongoDeploymentRepository()
        template = DeploymentTemplate(id=SAMPLE_VALID_OBJ_ID)
        try:
            repo.create_deployment_template(template)
        except Exception as error:
            self.fail(error)

    @patch(f"{REPO_PATH}.MongoDeploymentTemplateModel")
    def test_delete_deployment_template(self, mock_mongo_model):
        repo = MongoDeploymentRepository()
        mock_mongo_model.objects().delete = MagicMock(return_value=True)
        try:
            repo.delete_deployment_template(SAMPLE_VALID_OBJ_ID)
        except ObjectDoesNotExist:
            self.fail()

        mock_mongo_model.objects().delete = MagicMock(return_value=False)
        with self.assertRaises(ObjectDoesNotExist):
            repo.delete_deployment_template(SAMPLE_VALID_OBJ_ID)

    @patch(f"{REPO_PATH}.MongoDeploymentTemplateModel")
    def test_update_deployment_template(self, mock_mongo_model):
        repo = MongoDeploymentRepository()
        template = DeploymentTemplate(id=SAMPLE_VALID_OBJ_ID)
        mock_mongo_model.objects().first = MagicMock(return_value=None)
        with self.assertRaises(ObjectDoesNotExist):
            repo.update_deployment_template(SAMPLE_VALID_OBJ_ID, template)

        mock_mongo_model.objects().first = MagicMock(return_value={"a": "b"})
        repo.update_deployment_template(SAMPLE_VALID_OBJ_ID, template)

    @patch(INJECT_PATH, MagicMock())
    @patch(f"{REPO_PATH}.DeploymentRevision")
    def test__process_full_deployment_update(self, mock_deployment_revision):
        repo = MongoDeploymentRepository()
        deployment = Deployment(id=SAMPLE_VALID_OBJ_ID)
        mock_deployment_revision().to_dict = MagicMock(return_value={})

        class MockResult:
            inserted_id = SAMPLE_VALID_OBJ_ID

        self.db[repo.DEPLOYMENT_REVISION_COLLECTION].insert_one = MagicMock(
            return_value=MockResult
        )
        repo._process_full_deployment_update(deployment=deployment)

    def test__update_deployment(self):
        repo = MongoDeploymentRepository()
        self.db[repo.DEPLOYMENT_COLLECTION].find_one_and_update = MagicMock(
            return_value=None
        )
        with self.assertRaises(DeploymentDoesNotExist):
            repo._update_deployment(deployment_id=SAMPLE_VALID_OBJ_ID, content={})


if __name__ == "__main__":
    unittest.main()
