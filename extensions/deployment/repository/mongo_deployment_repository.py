from copy import copy
from datetime import datetime
from typing import Optional
import pymongo

from bson import ObjectId
from pymongo import MongoClient, WriteConcern
from pymongo.database import Database
from pymongo.read_concern import ReadConcern

from extensions.authorization.models.role.role import Role
from extensions.common.sort import SortField
from extensions.deployment.exceptions import (
    DeploymentDoesNotExist,
    DeploymentWithVersionNumberDoesNotExist,
)
from extensions.deployment.models.activation_code import ActivationCode
from extensions.deployment.models.care_plan_group import CarePlanGroup, CarePlanGroupLog
from extensions.deployment.models.deployment import (
    Deployment,
    Label,
    ModuleConfig,
    DeploymentRevision,
    OnboardingModuleConfig,
    ChangeType,
    DeploymentTemplate,
)
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    Learn,
    LearnArticle,
    LearnSection,
    OrderUpdateObject,
)
from extensions.deployment.models.status import Status
from extensions.deployment.models.user_note import UserNote
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.repository.models.mongo_deployment_template_model import (
    MongoDeploymentTemplateModel,
)
from extensions.exceptions import (
    LearnSectionDoesNotExist,
    LearnArticleDoesNotExist,
)
from extensions.utils import generate_code, format_sort_fields
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import escape
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.storage.model.file_storage import FileStorage


class MongoDeploymentRepository(DeploymentRepository):
    """Repository to work with deployment collection."""

    IGNORED_FIELDS = (
        Deployment.CREATE_DATE_TIME,
        Deployment.UPDATE_DATE_TIME,
    )

    DEPLOYMENT_COLLECTION = "deployment"
    CARE_PLAN_GROUP_LOG_COLLECTION = "careplangrouplog"
    OBSERVATION_NOTES_COLLECTION = "observationnotes"
    DEPLOYMENT_REVISION_COLLECTION = "deploymentrevision"
    STORAGE_COLLECTION = "filestorage"
    DEPLOYMENT_ID = "deploymentId"

    @autoparams()
    def __init__(self, database: Database, client: MongoClient):
        self._config = inject.instance(PhoenixServerConfig)
        self._db = database
        self._client = client

    def start_transaction(self):
        self.session = self._client.start_session()
        self.session.start_transaction(
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority", wtimeout=10000),
        )

    def commit_transactions(self):
        if self.session is not None:
            self.session.commit_transaction()
            self.session.end_session()
            self.session = None

    def cancel_transactions(self):
        if self.session is not None:
            self.session.end_session()
            self.session = None

    def generate_manager_code(self):
        length = ActivationCode.MANAGER_CODE_LENGTH
        return self.generate_activation_code(length, include_char=True)

    def generate_user_code(self):
        length = ActivationCode.USER_CODE_LENGTH
        return self.generate_activation_code(length, include_char=False)

    def generate_proxy_code(self):
        length = ActivationCode.USER_CODE_LENGTH  # keeping this same as for user
        return self.generate_activation_code(length, include_char=False)

    def generate_activation_code(self, length: int, include_char: bool) -> str:
        code = generate_code(length, include_char)
        duplicates_count: int = self._db[self.DEPLOYMENT_COLLECTION].count_documents(
            {"$or": [{"userActivationCode": code}, {"managerActivationCode": code}]}
        )
        # generate new code if this one is already occupied
        if duplicates_count > 0:
            code = self.generate_activation_code(length, include_char)
        return code

    def create_deployment_revision(self, deployment_revision: DeploymentRevision):
        document = deployment_revision.to_dict(ignored_fields=self.IGNORED_FIELDS)
        collection = self._db[self.DEPLOYMENT_REVISION_COLLECTION]
        result = collection.insert_one(
            remove_none_values(document), session=self.session
        )
        return str(result.inserted_id)

    """ Create document section """

    def create_deployment(self, deployment: Deployment) -> str:
        deployment.userActivationCode = self.generate_user_code()
        deployment.managerActivationCode = self.generate_manager_code()
        deployment.proxyActivationCode = self.generate_proxy_code()
        now = datetime.utcnow()
        deployment.createDateTime = deployment.updateDateTime = now

        deployment.moduleConfigs = []
        deployment.onboardingConfigs = []
        deployment.keyActions = []

        deployment.learn = Learn()
        deployment.learn.id = ObjectId()
        deployment.learn.createDateTime = deployment.learn.updateDateTime = now

        ignored_fields = (
            *self.IGNORED_FIELDS,
            f"{Deployment.LEARN}.{Learn.UPDATE_DATE_TIME}",
            f"{Deployment.LEARN}.{Learn.CREATE_DATE_TIME}",
        )
        deployment_dict = deployment.to_dict(ignored_fields=ignored_fields)
        deployment_dict = remove_none_values(deployment_dict)
        result = self._db[self.DEPLOYMENT_COLLECTION].insert_one(
            deployment_dict, session=self.session
        )
        return str(result.inserted_id)

    @id_as_obj_id
    def create_onboarding_module_config(
        self,
        deployment_id: str,
        config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        config.id = ObjectId()
        module_config_dict = remove_none_values(config.to_dict())
        query = {
            "$push": {Deployment.ONBOARDING_CONFIGS: module_config_dict},
            "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
        }
        if update_revision:
            query.update({"$inc": {Deployment.VERSION: 1}})

        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id}, query, session=self.session
        )
        if not result:
            raise DeploymentDoesNotExist

        return str(config.id)

    @id_as_obj_id
    def update_onboarding_module_config(
        self,
        deployment_id: str,
        onboarding_module_config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        onboarding_config_dict = remove_none_values(onboarding_module_config.to_dict())
        onboarding_module_config_id = ObjectId(onboarding_module_config.id)
        onboarding_config_dict[OnboardingModuleConfig.ID] = onboarding_module_config_id
        onboarding_config_set_dict = {Deployment.UPDATE_DATE_TIME: datetime.utcnow()}
        del onboarding_config_dict[OnboardingModuleConfig.VERSION]
        del onboarding_config_dict[OnboardingModuleConfig.ID]
        for key in onboarding_config_dict.keys():
            set_key = f"{Deployment.ONBOARDING_CONFIGS}.$[elem].{key}"
            onboarding_config_set_dict[set_key] = onboarding_config_dict[key]

        query = {"$set": onboarding_config_set_dict}
        if update_revision:
            inc_query = {
                Deployment.VERSION: 1,
                f"{Deployment.ONBOARDING_CONFIGS}.$[elem].{OnboardingModuleConfig.VERSION}": 1,
            }
            query.update({"$inc": inc_query})

        self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.ONBOARDING_CONFIGS}.id": onboarding_module_config_id,
            },
            query,
            array_filters=[{"elem.id": {"$eq": onboarding_module_config_id}}],
            session=self.session,
        )

        return str(onboarding_module_config_id)

    @id_as_obj_id
    def create_module_config(
        self, deployment_id: str, config: ModuleConfig, update_revision: bool = True
    ) -> str:
        config.id = ObjectId()
        module_config_dict = remove_none_values(
            config.to_dict(ignored_fields=self.IGNORED_FIELDS)
        )
        query = {"$push": {Deployment.MODULE_CONFIGS: module_config_dict}}
        if update_revision:
            query.update({"$inc": {Deployment.VERSION: 1}})
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id}, query, session=self.session
        )
        if not result:
            raise DeploymentDoesNotExist

        return str(config.id)

    @id_as_obj_id
    def update_module_config(
        self,
        deployment_id: str,
        config: ModuleConfig,
        update_revision: bool = True,
    ) -> str:
        module_config_set_dict = {}
        module_config_id = ObjectId(config.id)
        config.updateDateTime = datetime.utcnow()
        module_config_dict = remove_none_values(
            config.to_dict(ignored_fields=self.IGNORED_FIELDS)
        )
        del module_config_dict[ModuleConfig.VERSION]
        del module_config_dict[ModuleConfig.ID]
        for key in module_config_dict.keys():
            set_key = f"{Deployment.MODULE_CONFIGS}.$[elem].{key}"
            module_config_set_dict[set_key] = module_config_dict[key]

        query = {"$set": module_config_set_dict}
        if update_revision:
            inc_query = {
                Deployment.VERSION: 1,
                f"{Deployment.MODULE_CONFIGS}.$[elem].{ModuleConfig.VERSION}": 1,
            }
            query.update({"$inc": inc_query})

        self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.MODULE_CONFIGS}.id": module_config_id,
            },
            query,
            array_filters=[{"elem.id": {"$eq": module_config_id}}],
            session=self.session,
        )

        return str(module_config_id)

    @id_as_obj_id
    def create_key_action(self, deployment_id: str, key_action: KeyActionConfig) -> str:
        key_action.id = ObjectId()
        key_action.createDateTime = key_action.updateDateTime = datetime.utcnow()

        key_action_dict = key_action.to_dict(
            include_none=False,
            ignored_fields=self.IGNORED_FIELDS,
        )
        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {
                "$push": {Deployment.KEY_ACTIONS: key_action_dict},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            upsert=True,
            session=self.session,
        )
        if not result.matched_count:
            raise DeploymentDoesNotExist
        return str(key_action.id)

    @id_as_obj_id
    def create_learn_section(
        self, deployment_id: str, learn_section: LearnSection
    ) -> str:
        learn_section.createDateTime = learn_section.updateDateTime = datetime.utcnow()
        learn_section_dict = learn_section.to_dict(
            include_none=False,
            ignored_fields=self.IGNORED_FIELDS,
        )
        learn_section_dict[LearnSection.ID] = ObjectId()
        updated_result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {
                "$push": {f"{Deployment.LEARN}.{Learn.SECTIONS}": learn_section_dict},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if updated_result.modified_count == 0:
            raise DeploymentDoesNotExist
        return str(learn_section_dict[LearnSection.ID])

    @id_as_obj_id
    def create_learn_article(
        self, deployment_id: str, section_id: str, learn_article: LearnArticle
    ) -> str:
        learn_article.createDateTime = learn_article.updateDateTime = datetime.utcnow()
        learn_article.id = ObjectId()
        learn_article_dict = learn_article.to_dict(ignored_fields=self.IGNORED_FIELDS)
        push_key = f"{Deployment.LEARN}.{Learn.SECTIONS}.$.{LearnSection.ARTICLES}"
        updated_result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.LEARN}.{Learn.SECTION_ID}": section_id,
            },
            {
                "$push": {push_key: remove_none_values(learn_article_dict)},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if updated_result.modified_count == 0:
            raise DeploymentDoesNotExist

        return str(learn_article.id)

    """ END Create document section """

    """ Retrieve documents section """

    def retrieve_deployments(
        self,
        skip: int = 0,
        limit: int = None,
        search_criteria: str = None,
        sort_fields: list[SortField] = None,
        status: list[Status] = None,
        name_contains: str = None,
    ) -> tuple[list[Deployment], int]:
        formatted_sort = None
        status = [st.name for st in status] if status else None

        if sort_fields:
            formatted_sort = format_sort_fields(
                sort_fields=sort_fields,
                valid_sort_fields=Deployment.VALID_SORT_FIELDS,
            )

        filter_options = {Deployment.STATUS: status and {"$in": status}}
        if search_criteria:
            search = {"$regex": escape(search_criteria), "$options": "i"}
            text_search = {"$or": [{Deployment.ID: search}, {Deployment.NAME: search}]}
        else:
            text_search = None
            if name_contains:
                text_search = {
                    Deployment.NAME: {"$regex": escape(name_contains), "$options": "i"}
                }

        if text_search:
            filter_options.update(text_search)

        main_aggregation = []
        if formatted_sort:
            main_aggregation.append({"$sort": dict(formatted_sort)})
        main_aggregation.append({"$skip": skip or 0})
        if limit:
            main_aggregation.append({"$limit": limit})
        aggregation = [
            {"$addFields": {"id": {"$toString": "$_id"}}},
            {"$match": remove_none_values(filter_options)},
            {
                "$facet": {
                    "results": main_aggregation,
                    "totalCount": [{"$count": "count"}],
                }
            },
        ]
        result = self._db[self.DEPLOYMENT_COLLECTION].aggregate(aggregation)
        result = next(result)
        deployments_data = result["results"]
        deployments = [self.deployment_from_document(doc) for doc in deployments_data]

        if not result["totalCount"]:
            return deployments, 0

        return deployments, result["totalCount"][0]["count"]

    def retrieve_deployments_by_ids(
        self, deployment_ids: list[str]
    ) -> list[Deployment]:
        deployment_ids = [
            ObjectId(id_) for id_ in deployment_ids if ObjectId.is_valid(id_)
        ]
        result = self._db[self.DEPLOYMENT_COLLECTION].find(
            {Deployment.ID_: {"$in": deployment_ids}}
        )

        return [self.deployment_from_document(doc) for doc in result]

    def retrieve_deployment_codes(self, deployment_ids: list[str]) -> dict:
        deployment_ids = [ObjectId(id_) for id_ in deployment_ids]
        filter_options = {}
        if deployment_ids:
            filter_options.update({Deployment.ID_: {"$in": deployment_ids}})
        projection = {"code": 1}
        result = self._db[self.DEPLOYMENT_COLLECTION].find(filter_options, projection)
        return {str(item[Deployment.ID_]): item.get(Deployment.CODE) for item in result}

    @id_as_obj_id
    def retrieve_deployment_document(self, deployment_id: str) -> dict:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {Deployment.ID_: deployment_id}
        )
        if result is None:
            raise DeploymentDoesNotExist
        return result

    @id_as_obj_id
    def retrieve_deployment(self, deployment_id: str) -> Deployment:
        result = self.retrieve_deployment_document(deployment_id=deployment_id)
        return self.deployment_from_document(result)

    """ If the version does not exist in deployment then search in deploymentrevision """

    @id_as_obj_id
    def retrieve_deployment_by_version_number(
        self, deployment_id: str, version_number: int
    ) -> Deployment:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {Deployment.ID_: deployment_id, Deployment.VERSION: version_number}
        )
        if result is None:
            deployment_revision = self._db[
                self.DEPLOYMENT_REVISION_COLLECTION
            ].find_one(
                {self.DEPLOYMENT_ID: deployment_id, Deployment.VERSION: version_number}
            )
            if deployment_revision is None:
                if version_number == Deployment.FIRST_VERSION:
                    result = self._db[self.DEPLOYMENT_COLLECTION].find_one(
                        {Deployment.ID_: deployment_id}
                    )
                    if result is None:
                        raise DeploymentWithVersionNumberDoesNotExist
                else:
                    raise DeploymentWithVersionNumberDoesNotExist
            else:
                result = deployment_revision[DeploymentRevision.SNAP]

        return self.deployment_from_document(result)

    @id_as_obj_id
    def retrieve_deployment_revisions(
        self, deployment_id: str
    ) -> list[DeploymentRevision]:
        query = {DeploymentRevision.DEPLOYMENT_ID: deployment_id}
        revisions = self._db[self.DEPLOYMENT_REVISION_COLLECTION].find(query)
        revision_objects = []
        for revision_doc in revisions:
            revision = DeploymentRevision.from_dict(
                revision_doc, use_validator_field=False
            )
            revision.id = str(revision_doc[DeploymentRevision.ID_])
            revision_objects.append(revision)
        return revision_objects

    def retrieve_deployment_by_activation_code(
        self, deployment_code: str
    ) -> Deployment:
        query = {
            "$or": [
                {Deployment.USER_ACTIVATION_CODE: deployment_code},
                {Deployment.MANAGER_ACTIVATION_CODE: deployment_code},
                {Deployment.PROXY_ACTIVATION_CODE: deployment_code},
            ]
        }

        result = self._db[self.DEPLOYMENT_COLLECTION].find_one(query)

        if not result:
            raise DeploymentDoesNotExist

        return self.deployment_from_document(result)

    @id_as_obj_id
    def retrieve_module_configs(self, deployment_id: str) -> list[ModuleConfig]:
        coll = self._db.get_collection(self.DEPLOYMENT_COLLECTION)
        deployment = coll.find_one(
            {"_id": deployment_id}, projection={Deployment.MODULE_CONFIGS: 1, "_id": 0}
        )

        if deployment is None:
            raise DeploymentDoesNotExist

        if Deployment.MODULE_CONFIGS not in deployment:
            return []

        module_configs = []
        for conf_dict in deployment[Deployment.MODULE_CONFIGS]:
            module_config = ModuleConfig.from_dict(conf_dict, use_validator_field=False)
            if "id" in conf_dict:
                module_config.id = str(conf_dict["id"])
            module_configs.append(module_config)

        return module_configs

    def check_field_value_exists_in_module_configs(
        self, field_path: str, field_value: str
    ) -> bool:
        query = {f"moduleConfigs.{field_path}": field_value}
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one(query)
        return bool(result)

    @id_as_obj_id
    def retrieve_onboarding_module_configs(
        self, deployment_id: str
    ) -> list[OnboardingModuleConfig]:
        coll = self._db.get_collection(self.DEPLOYMENT_COLLECTION)
        deployment = coll.find_one(
            {"_id": deployment_id},
            projection={Deployment.ONBOARDING_CONFIGS: 1, "_id": 0},
        )

        if deployment is None:
            raise DeploymentDoesNotExist

        if Deployment.ONBOARDING_CONFIGS not in deployment:
            return []

        module_configs = []
        for conf_dict in deployment[Deployment.ONBOARDING_CONFIGS]:
            module_config = OnboardingModuleConfig.from_dict(conf_dict)
            if "id" in conf_dict:
                module_config.id = str(conf_dict["id"])
            module_configs.append(module_config)

        return module_configs

    def retrieve_article_by_id(
        self, article_id: str, deployment_id: str
    ) -> LearnArticle:
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        for section in deployment.learn.sections or []:
            for article in section.articles or []:
                if article.id == article_id:
                    return article
        raise ObjectDoesNotExist

    @id_as_obj_id
    def retrieve_module_config(self, module_config_id: str) -> Optional[ModuleConfig]:
        collection = self._db.get_collection(self.DEPLOYMENT_COLLECTION)
        deployment_dict = collection.find_one(
            {
                Deployment.MODULE_CONFIGS: {
                    "$elemMatch": {ModuleConfig.ID: module_config_id}
                }
            }
        )

        if not deployment_dict:
            return

        module_configs = deployment_dict.get(Deployment.MODULE_CONFIGS)
        module_config = next(
            filter(
                lambda config: config.get(ModuleConfig.ID) == module_config_id,
                module_configs,
            ),
            None,
        )
        return ModuleConfig.from_dict(module_config, use_validator_field=False)

    @id_as_obj_id
    def retrieve_key_actions(
        self, deployment_id: str, trigger: KeyActionConfig.Trigger = None
    ) -> list[KeyActionConfig]:
        query = {Deployment.ID_: deployment_id}
        if trigger:
            query[Deployment.KEY_ACTIONS] = {
                "$elemMatch": {KeyActionConfig.TRIGGER: trigger}
            }
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            remove_none_values(query)
        )
        if deployment:
            return [KeyActionConfig.from_dict(k) for k in deployment["keyActions"]]

    """ END Retrieve documents section """

    """ Update document section """

    def update_deployment(self, deployment: Deployment):
        deployment.validate_keys_should_not_be_present_on_update()
        deployment_dict = deployment.to_dict(ignored_fields=self.IGNORED_FIELDS)
        deployment_dict = remove_none_values(deployment_dict)
        deployment_id = deployment_dict.pop("id")
        content = {"$set": deployment_dict}
        self._update_deployment(deployment_id=deployment_id, content=content)
        return deployment.id

    @id_as_obj_id
    def _update_deployment(self, deployment_id: str, content: dict):
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id}, content, session=self.session
        )
        if not result:
            raise DeploymentDoesNotExist
        return result

    def _process_full_deployment_update(self, deployment: Deployment):
        consent_repo = inject.instance(ConsentRepository)
        consent_repo.session = self.session
        econsent_repo = inject.instance(EConsentRepository)
        econsent_repo.session = self.session

        initial_deployment_data = self.retrieve_deployment_document(
            deployment_id=deployment.id
        )

        deployment_revision = DeploymentRevision(
            deploymentId=deployment.id,
            snap=initial_deployment_data,
            changeType=ChangeType.MULTI_LANGUAGE_CONVERSION,
        )
        self.create_deployment_revision(deployment_revision=deployment_revision)

        if module_configs := deployment.moduleConfigs:
            if module_configs is not None:
                for module_config in module_configs:
                    self.update_module_config(
                        deployment_id=deployment.id,
                        config=module_config,
                        update_revision=False,
                    )
                deployment.moduleConfigs = None

        if onboarding_configs := deployment.onboardingConfigs:
            if onboarding_configs is not None:
                for onboarding_config in onboarding_configs:
                    self.update_onboarding_module_config(
                        deployment_id=deployment.id,
                        onboarding_module_config=onboarding_config,
                        update_revision=False,
                    )
                deployment.onboardingConfigs = None

        if roles := deployment.roles:
            self.create_or_update_roles(deployment_id=deployment.id, roles=roles)
            deployment.roles = None

        if deployment.learn and deployment.learn.sections:
            for learn_section in deployment.learn.sections:
                if learn_section.articles is not None:
                    for learn_article in learn_section.articles:
                        self.update_learn_article(
                            deployment_id=deployment.id,
                            section_id=learn_section.id,
                            article=learn_article,
                        )

                learn_section.articles = None
                self.update_learn_section(
                    deployment_id=deployment.id,
                    learn_section=learn_section,
                )
            deployment.learn = None

        if key_actions := deployment.keyActions:
            for key_action in key_actions:
                self.update_key_action(
                    deployment_id=deployment.id,
                    key_action=key_action,
                    key_action_id=key_action.id,
                )
            deployment.keyActions = None

        if consent := deployment.consent:
            consent_repo.create_consent(deployment_id=deployment.id, consent=consent)
            deployment.consent = None

        if econsent := deployment.econsent:
            econsent_repo.create_econsent(
                deployment_id=deployment.id, econsent=econsent
            )
            deployment.econsent = None

        deployment.version = None
        deployment_dict = deployment.to_dict(ignored_fields=self.IGNORED_FIELDS)
        deployment_dict = remove_none_values(deployment_dict)
        deployment_id = deployment_dict.pop("id")
        content = {
            "$inc": {Deployment.VERSION: 1},
            "$set": {
                **deployment_dict,
                Deployment.UPDATE_DATE_TIME: datetime.utcnow(),
            },
        }
        self._update_deployment(deployment_id=deployment_id, content=content)
        return deployment.id

    def update_full_deployment(self, deployment: Deployment) -> str:
        self.start_transaction()
        try:
            deployment_id = self._process_full_deployment_update(deployment=deployment)
        except Exception as e:
            self.cancel_transactions()
            raise e
        else:
            self.commit_transactions()
            return deployment_id

    @id_as_obj_id
    def update_enrollment_counter(self, deployment_id: str, **kwargs) -> Deployment:
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id},
            {"$inc": {Deployment.ENROLLMENT_COUNTER: 1}},
            return_document=True,
            session=kwargs.pop("session", None),
        )

        if not deployment:
            raise DeploymentDoesNotExist

        return self.deployment_from_document(deployment)

    @id_as_obj_id
    def update_learn_section(
        self, deployment_id: str, learn_section: LearnSection
    ) -> str:
        learn_section.updateDateTime = datetime.utcnow()
        learn_section_dict: dict = learn_section.to_dict(
            ignored_fields=self.IGNORED_FIELDS,
        )
        learn_section_dict = remove_none_values(learn_section_dict)
        update_dict = {
            f"{Deployment.LEARN}.{Learn.SECTIONS}.$.{key}": value
            for key, value in learn_section_dict.items()
            if key != "id"
        }
        learn_section_id = ObjectId(learn_section_dict[LearnSection.ID])
        updated_result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.LEARN}.{Learn.SECTION_ID}": learn_section_id,
            },
            {"$set": {**update_dict, Deployment.UPDATE_DATE_TIME: datetime.utcnow()}},
            session=self.session,
        )
        if updated_result.modified_count == 0:
            raise LearnSectionDoesNotExist
        return str(learn_section_dict[LearnSection.ID])

    @id_as_obj_id
    def update_learn_article(
        self,
        deployment_id: str,
        section_id: str,
        article: LearnArticle,
    ) -> str:
        article_dict = self.prepare_article_for_update(article, deployment_id)
        set_article_key = f"{Deployment.LEARN}.{Learn.SECTIONS}.$[section].{LearnSection.ARTICLES}.$[article]"
        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {
                "$set": {
                    set_article_key: article_dict,
                    Deployment.UPDATE_DATE_TIME: datetime.utcnow(),
                }
            },
            array_filters=[
                {"section.id": section_id},
                {"article.id": article_dict[LearnArticle.ID]},
            ],
            session=self.session,
        )
        if result.modified_count == 0:
            raise LearnArticleDoesNotExist
        return article.id

    def prepare_article_for_update(self, article: LearnArticle, deployment_id: str):
        old_article = self.retrieve_article_by_id(article.id, deployment_id)
        article.updateDateTime = datetime.utcnow()
        article.createDateTime = old_article.createDateTime

        article_dict = article.to_dict(ignored_fields=self.IGNORED_FIELDS)
        article_dict[LearnArticle.ID] = ObjectId(article.id)
        return remove_none_values(article_dict)

    @id_as_obj_id
    def update_key_action(
        self, deployment_id: str, key_action_id: str, key_action: KeyActionConfig
    ) -> tuple[str, bool]:
        key_action.id = key_action_id
        key_action.updateDateTime = datetime.utcnow()
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.KEY_ACTIONS}.id": key_action_id,
            }
        )
        if not deployment:
            raise ObjectDoesNotExist
        key_action_to_update = next(
            filter(
                lambda x: x[KeyActionConfig.ID] == key_action_id,
                [item for item in deployment[Deployment.KEY_ACTIONS]],
            )
        )
        update_required = not self._are_equal(
            remove_none_values(key_action_to_update),
            key_action.to_dict(include_none=False),
        )
        if update_required:
            key_action.createDateTime = key_action_to_update.pop(
                KeyActionConfig.CREATE_DATE_TIME, datetime.utcnow()
            )
            key_action_to_update.update(
                key_action.to_dict(
                    include_none=False,
                    ignored_fields=self.IGNORED_FIELDS,
                )
            )
            if key_action.notifyEvery is None:
                key_action_to_update.pop(KeyActionConfig.NOTIFY_EVERY, None)
            self._db[self.DEPLOYMENT_COLLECTION].update_one(
                {
                    Deployment.ID_: deployment_id,
                    f"{Deployment.KEY_ACTIONS}.id": key_action_id,
                },
                {
                    "$set": {
                        f"{Deployment.KEY_ACTIONS}.$[elem]": key_action_to_update,
                        Deployment.UPDATE_DATE_TIME: datetime.utcnow(),
                    }
                },
                array_filters=[{"elem.id": {"$eq": key_action_id}}],
                session=self.session,
            )
        return str(key_action_id), update_required

    """ END Update document section """

    """ Delete document section """

    @id_as_obj_id
    def delete_deployment(self, deployment_id: str) -> str:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_delete(
            {Deployment.ID_: ObjectId()}, session=self.session
        )
        if result is None:
            raise DeploymentDoesNotExist

        return str(deployment_id)

    @id_as_obj_id
    def delete_module_config(self, deployment_id: str, module_config_id: str) -> None:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id},
            {
                "$pull": {
                    Deployment.MODULE_CONFIGS: {ModuleConfig.ID: module_config_id}
                },
                "$inc": {Deployment.VERSION: 1},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if result is None:
            raise DeploymentDoesNotExist

    @id_as_obj_id
    def delete_onboarding_module_config(
        self, deployment_id: str, onboarding_config_id: str
    ) -> None:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id},
            {
                "$pull": {
                    Deployment.ONBOARDING_CONFIGS: {
                        OnboardingModuleConfig.ID: onboarding_config_id
                    }
                },
                "$inc": {Deployment.VERSION: 1},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if result is None:
            raise DeploymentDoesNotExist

    @id_as_obj_id
    def delete_learn_section(self, deployment_id: str, section_id: str):
        pull_key = f"{Deployment.LEARN}.{Learn.SECTIONS}"
        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {
                "$pull": {pull_key: {LearnSection.ID: section_id}},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if not result.modified_count:
            raise ObjectDoesNotExist

    @id_as_obj_id
    def delete_learn_article(
        self, deployment_id: str, section_id: str, article_id: str
    ):
        pull_key = f"{Deployment.LEARN}.{Learn.SECTIONS}.$.{LearnSection.ARTICLES}"
        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {
                Deployment.ID_: deployment_id,
                f"{Deployment.LEARN}.{Learn.SECTION_ID}": section_id,
            },
            {
                "$pull": {pull_key: {"id": article_id}},
                "$set": {Deployment.UPDATE_DATE_TIME: datetime.utcnow()},
            },
            session=self.session,
        )
        if not result.modified_count:
            raise ObjectDoesNotExist

    @id_as_obj_id
    def delete_key_action(self, deployment_id: str, key_action_id: str) -> None:
        result = self._db.get_collection(self.DEPLOYMENT_COLLECTION).update_one(
            {Deployment.ID_: deployment_id},
            {"$pull": {Deployment.KEY_ACTIONS: {KeyActionConfig.ID: key_action_id}}},
            session=self.session,
        )
        if not result.matched_count:
            raise DeploymentDoesNotExist
        if not result.modified_count:
            raise ObjectDoesNotExist

    """ END Delete document section """

    @staticmethod
    def _are_equal(dict1, dict2) -> bool:
        dict1 = copy(dict1)
        dict2 = copy(dict2)
        for _dict in (dict1, dict2):
            _dict.pop("createDateTime", None)
            _dict.pop("updateDateTime", None)
            _dict.pop("version", None)

        return dict1 == dict2

    @id_as_obj_id
    def create_care_plan_group(
        self, deployment_id: str, care_plan_group: CarePlanGroup
    ) -> bool:
        care_plan_group_dict = remove_none_values(care_plan_group.to_dict())
        modified_count = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$set": {Deployment.CARE_PLAN_GROUP: care_plan_group_dict}},
            session=self.session,
        )
        return modified_count == 1

    @id_as_obj_id
    def create_or_update_roles(
        self, deployment_id: str, roles: list[Role]
    ) -> list[str]:
        roles_dicts = []

        for role in roles:
            role.id = role.id or str(ObjectId())
            role_dict = role.to_dict(include_none=False)
            role_dict[Role.ID] = ObjectId(role.id)
            roles_dicts.append(role_dict)

        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$set": {Deployment.ROLES: roles_dicts}},
            session=self.session,
        )

        if not result.matched_count:
            raise DeploymentDoesNotExist

        return [role.id for role in roles]

    @id_as_obj_id
    def retrieve_user_care_plan_group_log(
        self, deployment_id: str, user_id: str
    ) -> list[CarePlanGroupLog]:
        logs_dict = self._db.get_collection(self.CARE_PLAN_GROUP_LOG_COLLECTION).find(
            {
                CarePlanGroupLog.USER_ID: user_id,
                CarePlanGroupLog.DEPLOYMENT_ID: deployment_id,
            }
        )

        if not logs_dict:
            return []
        logs = []

        for log in logs_dict:
            care_plan_group_log_id = log.pop(CarePlanGroupLog.ID)
            care_plan_group_log_obj = CarePlanGroupLog.from_dict(log)
            care_plan_group_log_obj.id = str(care_plan_group_log_id)
            logs.append(care_plan_group_log_obj)

        return logs

    @id_as_obj_id
    def retrieve_user_notes(self, deployment_id: str, user_id: str) -> list[UserNote]:
        logs_dict = self._db.get_collection(self.CARE_PLAN_GROUP_LOG_COLLECTION).find(
            {
                CarePlanGroupLog.USER_ID: user_id,
                CarePlanGroupLog.DEPLOYMENT_ID: deployment_id,
            }
        )

        if not logs_dict:
            return []
        logs = []

        for log in logs_dict:
            note = UserNote.from_dict(
                {**log, UserNote.TYPE: UserNote.UserNoteType.CAREPLANGROUPLOG.value}
            )
            note.id = str(log[CarePlanGroupLog.ID])
            logs.append(note)

        return logs

    def add_user_observation_note(self, user_note: UserNote) -> str:
        collection = self._db.get_collection(self.OBSERVATION_NOTES_COLLECTION)
        user_note_dict = remove_none_values(user_note.to_dict())
        result = collection.insert_one(user_note_dict, session=self.session)
        return str(result.inserted_id)

    def retrieve_user_observation_notes(
        self, deployment_id: str, user_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserNote], int]:
        collection = self._db.get_collection(self.OBSERVATION_NOTES_COLLECTION)
        query = {UserNote.USER_ID: user_id, UserNote.DEPLOYMENT_ID: deployment_id}
        results = (
            collection.find(query)
            .sort(UserNote.CREATE_DATE_TIME, pymongo.DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        user_notes_count = results.count()
        user_notes = [
            UserNote.from_dict(
                {
                    UserNote.ID: str(result.pop(UserNote.ID_)),
                    UserNote.TYPE: UserNote.UserNoteType.USER_OBSERVATION_NOTES.value,
                    **result,
                }
            )
            for result in results
        ]
        return user_notes, user_notes_count

    @id_as_obj_id
    def update_localizations(self, deployment_id: str, localizations: dict) -> str:
        deployment = self._db[self.DEPLOYMENT_COLLECTION].find_one_and_update(
            {Deployment.ID_: deployment_id},
            {
                "$set": {
                    Deployment.LOCALIZATIONS: localizations,
                    Deployment.UPDATE_DATE_TIME: datetime.utcnow(),
                }
            },
            session=self.session,
        )
        if not deployment:
            raise DeploymentDoesNotExist
        return str(deployment_id)

    @id_as_obj_id
    def retrieve_localization(self, deployment_id: str, locale: str) -> dict:
        result = self._db[self.DEPLOYMENT_COLLECTION].find_one(
            {Deployment.ID_: deployment_id}
        )
        if result is None:
            raise DeploymentDoesNotExist

        localizations_data = result.get(Deployment.LOCALIZATIONS, {})
        return localizations_data.get(locale) or localizations_data.get(Language.EN, {})

    @staticmethod
    def deployment_from_document(doc: dict) -> Deployment:
        deployment = Deployment.from_dict(doc, use_validator_field=False)
        if not deployment.id:
            deployment.id = str(doc[Deployment.ID_])
        return deployment

    @id_as_obj_id
    def reorder_learn_sections(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):
        field = f"{Deployment.LEARN}.{Learn.SECTIONS}"
        updated_time = datetime.utcnow()
        for learn_section in ordering_data:
            result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
                {
                    Deployment.ID_: deployment_id,
                    f"{field}.{LearnSection.ID}": ObjectId(learn_section.id),
                },
                {
                    "$set": {
                        f"{field}.$.{LearnSection.ORDER}": learn_section.order,
                        f"{field}.$.{LearnSection.UPDATE_DATE_TIME}": updated_time,
                        f"{Deployment.UPDATE_DATE_TIME}": updated_time,
                    }
                },
                session=self.session,
            )
            if not result.modified_count:
                raise ObjectDoesNotExist

    @id_as_obj_id
    def reorder_learn_articles(
        self,
        deployment_id: str,
        section_id: str,
        ordering_data: list[OrderUpdateObject],
    ):
        field = f"{Deployment.LEARN}.{Learn.SECTIONS}.$[section].{LearnSection.ARTICLES}.$[article]"
        updated_time = datetime.utcnow()
        for learn_article in ordering_data:
            result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
                {Deployment.ID_: deployment_id},
                {
                    "$set": {
                        f"{field}.{LearnArticle.ORDER}": learn_article.order,
                        f"{field}.{LearnArticle.UPDATE_DATE_TIME}": updated_time,
                        f"{Deployment.UPDATE_DATE_TIME}": updated_time,
                    }
                },
                array_filters=[
                    {"section.id": ObjectId(section_id)},
                    {"article.id": ObjectId(learn_article.id)},
                ],
                session=self.session,
            )
            if not result.modified_count:
                raise ObjectDoesNotExist

    @id_as_obj_id
    def reorder_module_configs(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):
        updated_time = datetime.utcnow()

        inc_query = {
            Deployment.VERSION: 1,
            f"{Deployment.MODULE_CONFIGS}.$.{ModuleConfig.VERSION}": 1,
        }

        for module_config in ordering_data:
            query = {
                "$set": {
                    f"{Deployment.MODULE_CONFIGS}.$.{ModuleConfig.ORDER}": module_config.order,
                    f"{Deployment.MODULE_CONFIGS}.$.{ModuleConfig.UPDATE_DATE_TIME}": updated_time,
                    f"{Deployment.UPDATE_DATE_TIME}": updated_time,
                },
                "$inc": inc_query,
            }
            result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
                {
                    Deployment.ID_: deployment_id,
                    f"{Deployment.MODULE_CONFIGS}.{ModuleConfig.ID}": ObjectId(
                        module_config.id
                    ),
                },
                query,
                session=self.session,
            )
            if not result.modified_count:
                raise ObjectDoesNotExist

    @id_as_obj_id
    def reorder_onboarding_module_configs(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):

        inc_query = {
            Deployment.VERSION: 1,
            f"{Deployment.ONBOARDING_CONFIGS}.$.{OnboardingModuleConfig.VERSION}": 1,
        }
        for onboarding_config in ordering_data:
            order_key = (
                f"{Deployment.ONBOARDING_CONFIGS}.$.{OnboardingModuleConfig.ORDER}"
            )
            query = {
                "$set": {
                    order_key: onboarding_config.order,
                    f"{Deployment.UPDATE_DATE_TIME}": datetime.utcnow(),
                },
                "$inc": inc_query,
            }
            result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
                {
                    Deployment.ID_: deployment_id,
                    f"{Deployment.ONBOARDING_CONFIGS}.{OnboardingModuleConfig.ID}": ObjectId(
                        onboarding_config.id
                    ),
                },
                query,
                session=self.session,
            )
            if not result.modified_count:
                raise ObjectDoesNotExist

    def retrieve_deployment_revision_by_module_config_version(
        self,
        deployment_id: str,
        module_id: str,
        module_config_version: int,
        module_config_id: str = None,
        config_body_id: str = None,
    ) -> Optional[DeploymentRevision]:
        if module_config_version is None:
            module_config_version = {"$exists": False}
        module_config_query = {
            "$elemMatch": remove_none_values(
                {
                    ModuleConfig.MODULE_ID: module_id,
                    ModuleConfig.ID: module_config_id,
                    ModuleConfig.VERSION: module_config_version,
                    f"{ModuleConfig.CONFIG_BODY}.id": config_body_id,
                }
            )
        }
        query = {
            DeploymentRevision.DEPLOYMENT_ID: ObjectId(deployment_id),
            f"{DeploymentRevision.SNAP}.{Deployment.MODULE_CONFIGS}": module_config_query,
        }
        revision_data = self._db[self.DEPLOYMENT_REVISION_COLLECTION].find_one(query)
        if not revision_data:
            return
        revision = DeploymentRevision.from_dict(
            revision_data, use_validator_field=False
        )
        revision.id = str(revision_data[DeploymentRevision.ID_])
        return revision

    def create_deployment_template(self, template: DeploymentTemplate) -> str:
        template.createDateTime = template.updateDateTime = datetime.utcnow()
        new_event: MongoDeploymentTemplateModel = MongoDeploymentTemplateModel(
            **template.to_dict(include_none=False)
        )
        return str(new_event.save().id)

    def retrieve_deployment_templates(
        self, organization_id: str = None
    ) -> list[DeploymentTemplate]:
        if organization_id:
            results = MongoDeploymentTemplateModel.objects(
                organizationIds=organization_id
            )
        else:
            results = MongoDeploymentTemplateModel.objects()
        return [DeploymentTemplate.from_dict(i.to_dict()) for i in results]

    def retrieve_deployment_template(self, template_id: str) -> DeploymentTemplate:
        res = MongoDeploymentTemplateModel.objects(id=template_id).first()
        if not res:
            raise ObjectDoesNotExist(f"Template {template_id} does not exist")

        return DeploymentTemplate.from_dict(res.to_dict())

    def delete_deployment_template(self, template_id: str):
        deleted = MongoDeploymentTemplateModel.objects(id=template_id).delete()
        if not deleted:
            raise ObjectDoesNotExist

    def update_deployment_template(
        self, template_id: str, template: DeploymentTemplate
    ) -> str:
        old_template = MongoDeploymentTemplateModel.objects(id=template_id).first()
        if not old_template:
            raise ObjectDoesNotExist
        data = template.to_dict(include_none=False)
        old_template.update(**data)
        return template_id

    def retrieve_files_in_library(
        self,
        library_id: str,
        deployment_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ):
        match_query = {
            f"{FileStorage.METADATA}.libraryId": library_id,
            f"{FileStorage.METADATA}.deploymentId": deployment_id,
        }
        results = (
            self._db[self.STORAGE_COLLECTION]
            .find(remove_none_values(match_query))
            .skip(offset)
            .limit(limit)
        )
        files = []
        for result in results:
            result[FileStorage.ID] = str(result.pop(FileStorage.ID_))
            file = FileStorage.from_dict(result)
            files.append(file)
        return files

    @id_as_obj_id
    def create_deployment_labels(self, deployment_id: str, labels: list[Label]):
        labels_dicts = []
        for label in labels:
            label.createDateTime = datetime.now()
            label_dict = label.to_dict(include_none=False)
            label_dict[Label.ID] = ObjectId()
            label_dict[Label.AUTHOR_ID] = ObjectId(label.authorId)
            labels_dicts.append(label_dict)

        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$push": {f"{Deployment.LABELS}": {"$each": labels_dicts}}},
            session=self.session,
        )
        if not result.matched_count:
            raise DeploymentDoesNotExist
        return [str(label[Label.ID]) for label in labels_dicts]

    @id_as_obj_id
    def retrieve_deployment_labels(self, deployment_id: str) -> list[Label]:
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        if not deployment.features.labels:
            raise ObjectDoesNotExist(message="Label feature is not enabled")
        return deployment.labels

    @id_as_obj_id
    def update_deployment_labels(
        self,
        deployment_id: str,
        labels: list[Label],
        updated_label: Optional[Label] = None,
    ):
        if updated_label:
            label_index = self.find_label_index_in_labels(updated_label.id, labels)
            labels[label_index].text = updated_label.text
            labels[label_index].updatedBy = updated_label.updatedBy
            labels[label_index].updateDateTime = datetime.now()

        updated_labels_dicts = list()

        for label in labels:
            label_dict = label.to_dict(include_none=False)
            label_dict[Label.ID] = ObjectId(label.id)
            label_dict[Label.AUTHOR_ID] = ObjectId(label.authorId)
            if label.updatedBy:
                label_dict[Label.UPDATED_BY] = ObjectId(label.updatedBy)
            updated_labels_dicts.append(label_dict)

        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$set": {f"{Deployment.LABELS}": updated_labels_dicts}},
            session=self.session,
        )
        if not result.matched_count:
            raise DeploymentDoesNotExist
        return str(deployment_id)

    @id_as_obj_id
    def delete_deployment_label(self, deployment_id: str, label_id: str):

        result = self._db[self.DEPLOYMENT_COLLECTION].update_one(
            {Deployment.ID_: deployment_id},
            {"$pull": {f"{Deployment.LABELS}": {Label.ID: label_id}}},
            session=self.session,
        )
        if not result.matched_count:
            raise DeploymentDoesNotExist
        if not result.modified_count:
            raise ObjectDoesNotExist("Label does not exist in deployment")

    def find_label_index_in_labels(self, label_id, labels: list[Label]) -> int:
        if not labels:
            raise ObjectDoesNotExist(message=f"Label with {label_id} doesn't exist")
        label_index = self._find_label_index_in_labels(str(label_id), labels)
        if label_index is None:
            raise ObjectDoesNotExist(message=f"Label with {label_id} doesn't exist")
        return label_index

    def _find_label_index_in_labels(
        self, label_id, labels: list[Label]
    ) -> Optional[int]:
        n = 0
        for label in labels:
            if label.id == label_id:
                return n
            n += 1
