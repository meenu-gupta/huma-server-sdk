from copy import copy
from functools import cached_property

from extensions.authorization.models.role.role import Role
from extensions.common.s3object import S3Object
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import (
    Deployment,
    ModuleConfig,
    OnboardingModuleConfig,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import Learn, LearnSection, LearnArticle
from extensions.deployment.models.status import Status
from extensions.deployment.router.deployment_requests import (
    CloneDeploymentRequestObject,
    UpdateDeploymentRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.deployment.exceptions import InvalidDeploymentException
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


def skip_if_none(f):
    def wrapper(self, *args, **kwargs):
        if args:
            if not any(args):
                return
        if kwargs:
            if not any(kwargs.values()):
                return
        return f(self, *args, **kwargs)

    return wrapper


class CloneDeploymentUseCase(UseCase):
    COMMON_RESET_FIELDS = (
        Deployment.CREATE_DATE_TIME,
        Deployment.ID,
        Deployment.UPDATE_DATE_TIME,
    )
    RESET_FIELDS = (
        Deployment.CONSENT,
        Deployment.ECONSENT,
        Deployment.ENROLLMENT_COUNTER,
        Deployment.KEY_ACTIONS,
        Deployment.LEARN,
        Deployment.MANAGER_ACTIVATION_CODE,
        Deployment.MODULE_CONFIGS,
        Deployment.ONBOARDING_CONFIGS,
        Deployment.ROLES,
        Deployment.PROXY_ACTIVATION_CODE,
        Deployment.STATS,
        Deployment.USER_ACTIVATION_CODE,
        Deployment.VERSION,
        *COMMON_RESET_FIELDS,
    )
    request_object: CloneDeploymentRequestObject
    new_deployment_id: str

    @autoparams()
    def __init__(self, file_storage: FileStorageAdapter):
        self._article_ids = {}
        self._file_storage = file_storage
        self._service = DeploymentService()
        self._module_config_ids = {}

    def execute(self, request_object):
        self.request_object = request_object
        return super(CloneDeploymentUseCase, self).execute(request_object)

    def process_request(self, request_object: CloneDeploymentRequestObject):
        deployment = copy(self.deployment)

        self._check_bucket_exists()
        self._create_deployment(copy(self.deployment), request_object.name)
        self._copy_consent(deployment.consent)
        self._copy_econsent(deployment.econsent)
        self._copy_onboarding_configs(deployment.onboardingConfigs)
        self._copy_roles(deployment.roles)
        self._copy_learn(deployment.learn)
        self._copy_module_configs(deployment.moduleConfigs)
        self._copy_key_actions(deployment.keyActions)
        return Response(value=self.new_deployment_id)

    @cached_property
    def deployment(self):
        return self._service.retrieve_deployment(self.request_object.referenceId)

    def _check_bucket_exists(self):
        icon: S3Object = self.deployment.icon
        if icon and not self._file_storage.file_exist(icon.bucket, icon.key):
            raise InvalidDeploymentException("Target deployment has assets issue")

    def _create_deployment(self, ref_dep: Deployment, dep_name: str):
        ref_dep.reset_attributes(self.RESET_FIELDS)
        ref_dep.name = dep_name
        ref_dep.status = Status.DRAFT
        self.new_deployment_id = self._service.create_deployment(ref_dep)
        if ref_dep.icon:
            self._update_deployment_icon(ref_dep.icon)

    def _copy_file(self, file_obj: S3Object) -> S3Object:
        filename = file_obj.key.replace(
            self.request_object.referenceId, self.new_deployment_id
        )
        self._file_storage.copy(file_obj.key, filename, file_obj.bucket)
        return S3Object.from_dict(
            {
                S3Object.BUCKET: file_obj.bucket,
                S3Object.KEY: filename,
                S3Object.REGION: file_obj.region,
            }
        )

    def _update_deployment_icon(self, icon: S3Object) -> str:
        new_icon = self._copy_file(icon)
        return self._service.update_deployment(
            UpdateDeploymentRequestObject(icon=new_icon, id=self.new_deployment_id),
            update_revision=False,
        )

    @skip_if_none
    def _copy_consent(self, consent: Consent):
        fields = (*self.COMMON_RESET_FIELDS, Consent.REVISION)
        consent.reset_attributes(fields)
        self._service.create_consent(self.new_deployment_id, consent)

    @skip_if_none
    def _copy_econsent(self, econsent: EConsent):
        fields = (*self.COMMON_RESET_FIELDS, EConsent.REVISION)
        econsent.reset_attributes(fields)
        if not econsent.sections:
            return self._service.create_econsent(self.new_deployment_id, econsent)

        for section in econsent.sections:
            if section.videoLocation:
                file_obj = self._copy_file(section.videoLocation)
                section.videoLocation = file_obj
            if section.thumbnailLocation:
                file_obj = self._copy_file(section.thumbnailLocation)
                section.thumbnailLocation = file_obj

        self._service.create_econsent(self.new_deployment_id, econsent)

    @skip_if_none
    def _copy_learn(self, learn: Learn):
        for section in learn.sections or []:
            backup_section = copy(section)
            section.reset_attributes({*self.COMMON_RESET_FIELDS, LearnSection.ARTICLES})
            section_id = self._service.create_learn_section(
                deployment_id=self.new_deployment_id, learn_section=section
            )
            if not backup_section.articles:
                continue
            self._copy_articles(backup_section.articles, section_id)

    @skip_if_none
    def _copy_articles(self, articles: list[LearnArticle], section_id: str):
        for article in articles:
            article_id = article.id
            article.reset_attributes(self.COMMON_RESET_FIELDS)
            if article.thumbnailUrl:
                file_obj = self._copy_file(article.thumbnailUrl)
                article.thumbnailUrl = file_obj
            if article.content and article.content.videoUrl:
                file_obj = self._copy_file(article.content.videoUrl)
                article.content.videoUrl = file_obj
            object_id = self._service.create_article(
                deployment_id=self.new_deployment_id,
                section_id=section_id,
                learn_article=article,
            )
            self._article_ids.update({article_id: object_id})

    @skip_if_none
    def _copy_module_configs(self, module_configs: list[ModuleConfig]):
        for mc in module_configs:
            config_id = mc.id
            mc.reset_attributes(self.COMMON_RESET_FIELDS)
            mc.learnArticleIds = self._rebind_articles(mc.learnArticleIds)
            object_id = self._service.create_module_config(
                deployment_id=self.new_deployment_id,
                config=mc,
                update_revision=False,
            )
            self._module_config_ids.update({config_id: object_id})

    @skip_if_none
    def _copy_key_actions(self, key_actions: list[KeyActionConfig]):
        for ka in key_actions:
            ka.reset_attributes(self.COMMON_RESET_FIELDS)
            ka.moduleConfigId = self._module_config_ids.get(ka.moduleConfigId)
            ka.learnArticleId = self._article_ids.get(ka.learnArticleId)
            self._service.create_key_action(
                deployment_id=self.new_deployment_id, key_action=ka
            )

    @skip_if_none
    def _copy_onboarding_configs(
        self, onboarding_configs: list[OnboardingModuleConfig]
    ):
        for onboarding_config in onboarding_configs:
            onboarding_config.reset_attributes(self.COMMON_RESET_FIELDS)
            self._service.create_onboarding_module_config(
                self.new_deployment_id,
                onboarding_config,
                update_revision=False,
            )

    @skip_if_none
    def _copy_roles(self, roles: list[Role]):
        for role in roles:
            role.reset_attributes(self.COMMON_RESET_FIELDS)
        return self._service.create_or_update_roles(
            deployment_id=self.new_deployment_id, roles=roles
        )

    @skip_if_none
    def _rebind_articles(self, article_ids: list[str]):
        article_ids = [self._article_ids.get(id_) for id_ in article_ids]
        return list(filter(None, article_ids))
