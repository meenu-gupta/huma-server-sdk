from functools import cached_property
import logging
import typing
from copy import copy
from datetime import datetime
from typing import Optional

from extensions.authorization.exceptions import WrongActivationOrMasterKeyException
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.services.authorization import AuthorizationService
from extensions.common.sort import SortField
from extensions.deployment.events import (
    CreateDeploymentEvent,
    DeleteDeploymentEvent,
    PostUpdateKeyActionConfigEvent,
    PostDeleteKeyActionConfigEvent,
    PostCreateKeyActionConfigEvent,
    PreDeploymentUpdateEvent,
    PostDeploymentUpdateEvent,
)
from extensions.deployment.events.delete_custom_roles_event import (
    DeleteDeploymentCustomRolesEvent,
)
from extensions.deployment.exceptions import (
    DeploymentDoesNotExist,
    EConsentLogDoesNotExist,
    ModuleWithPrimitiveDoesNotExistException,
)
from extensions.deployment.models.activation_code import ActivationCode
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroup,
    CarePlanGroupLog,
)
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import (
    Deployment,
    ModuleConfig,
    OnboardingModuleConfig,
    ChangeType,
    DeploymentRevision,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    LearnSection,
    LearnArticle,
)
from extensions.deployment.models.status import Status
from extensions.deployment.models.user_note import UserNote
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.exceptions import EncryptionSecretNotAvailable
from extensions.module_result.models.module_config import Footnote
from extensions.module_result.modules import (
    excluded_modules_ids_for_applying_default_disclaimer_config,
    excluded_questionnaire_types_for_applying_default_disclaimer_config,
)
from extensions.module_result.modules.awareness_training import AwarenessTrainingModule
from extensions.module_result.modules.az_screening_questionnaire import (
    AZScreeningQuestionnaireModule,
)
from extensions.module_result.modules.background_information import (
    BackgroundInformationModule,
)
from extensions.module_result.modules.ecg_module.ecg_healthkit import ECGHealthKitModule
from extensions.module_result.modules.high_frequency_step import HighFrequencyStepModule
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.module_result.modules.step import StepModule
from extensions.module_result.modules.surgery_details import SurgeryDetailsModule
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import get_all_subclasses
from sdk.common.utils.encryption_utils import encrypt
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class DeploymentService:
    """Service to work with deployment repo."""

    @autoparams()
    def __init__(
        self,
        repo: DeploymentRepository,
        consent_repo: ConsentRepository,
        config: PhoenixServerConfig,
        econsent_repo: EConsentRepository,
        modules_manager: ModulesManager,
        event_bus: EventBusAdapter,
        submitter_id: str = None,
    ):
        self.repo = repo
        self.consent_repo = consent_repo
        self.econsent_repo = econsent_repo
        self.modules_manager = modules_manager
        self.config = config
        self._event_bus = event_bus
        self.submitter_id = submitter_id or None

    def create_deployment(self, deployment: Deployment) -> str:
        deployment_id = self.repo.create_deployment(deployment=deployment)
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(CreateDeploymentEvent(deployment_id))
        return deployment_id

    def create_deployment_revision(
        self,
        deployment: Deployment,
        change_type: ChangeType,
        submitter_id: str,
        change_id: str,
    ):
        revision_data = {
            DeploymentRevision.CHANGE_TYPE: change_type.value,
            DeploymentRevision.VERSION: deployment.version,
            DeploymentRevision.SUBMITTER_ID: submitter_id,
            DeploymentRevision.DEPLOYMENT_ID: deployment.id,
            DeploymentRevision.SNAP: deployment,
        }
        if change_type == ChangeType.MODULE_CONFIG:
            revision_data.update({DeploymentRevision.MODULE_CONFIG_ID: change_id})
        elif change_type == ChangeType.ONBOARDING_CONFIG:
            revision_data.update({DeploymentRevision.ONBOARDING_CONFIG_ID: change_id})

        clear_data = remove_none_values(revision_data)
        deployment_revision = DeploymentRevision.from_dict(clear_data)
        return self.repo.create_deployment_revision(
            deployment_revision=deployment_revision
        )

    def create_consent(self, deployment_id: str, consent: Consent) -> str:
        return self.consent_repo.create_consent(
            deployment_id=deployment_id, consent=consent
        )

    def create_consent_log(self, deployment_id: str, consent_log: ConsentLog) -> str:
        return self.consent_repo.create_consent_log(
            deployment_id=deployment_id, consent_log=consent_log
        )

    def create_or_update_module_config(
        self, deployment_id: str, config: ModuleConfig
    ) -> str:
        module_configs = self.retrieve_module_configs(deployment_id)
        module_in_db = [mc for mc in module_configs if mc.id == config.id]
        if module_in_db:
            return self.update_module_config(deployment_id, config)
        return self.create_module_config(deployment_id, config)

    def create_module_config(
        self, deployment_id: str, config: ModuleConfig, update_revision: bool = True
    ) -> str:
        self.modules_manager.has(config.moduleId, raise_error=True)
        config.createDateTime = config.updateDateTime = datetime.utcnow()
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        config_id = self.repo.create_module_config(
            deployment_id=deployment_id,
            config=config,
            update_revision=update_revision,
        )
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.MODULE_CONFIG,
            submitter_id=self.submitter_id,
            change_id=config.id,
        )
        return config_id

    def update_module_config(
        self, deployment_id: str, config: ModuleConfig, update_revision: bool = True
    ) -> str:
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        config_id = self.repo.update_module_config(
            deployment_id=deployment_id,
            config=config,
            update_revision=update_revision,
        )
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.MODULE_CONFIG,
            submitter_id=self.submitter_id,
            change_id=config.id,
        )
        return config_id

    @staticmethod
    def _are_deployments_dicts_equal(dict1, dict2) -> bool:
        dict1 = copy(dict1)
        dict2 = copy(dict2)
        for _dict in (dict1, dict2):
            _dict.pop(Deployment.CREATE_DATE_TIME, None)
            _dict.pop(Deployment.UPDATE_DATE_TIME, None)
            _dict.pop(Deployment.VERSION, None)

        return dict1 == dict2

    def create_learn_section(
        self, deployment_id: str, learn_section: LearnSection
    ) -> str:
        return self.repo.create_learn_section(
            deployment_id=deployment_id, learn_section=learn_section
        )

    def create_or_update_onboarding_module_config(
        self, deployment_id: str, config: OnboardingModuleConfig
    ) -> str:
        module_configs = self.retrieve_onboarding_module_configs(
            deployment_id=deployment_id
        )
        module_in_db = [mc for mc in module_configs if mc.id == config.id]
        if not module_in_db:
            return self.create_onboarding_module_config(deployment_id, config)
        return self.update_onboarding_module_config(deployment_id, config)

    def create_onboarding_module_config(
        self,
        deployment_id: str,
        config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        from extensions.authorization.boarding.manager import BoardingManager

        BoardingManager.has(config.onboardingId, raise_error=True)
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        config_id = self.repo.create_onboarding_module_config(
            deployment_id=deployment_id, config=config, update_revision=update_revision
        )
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.ONBOARDING_CONFIG,
            submitter_id=self.submitter_id,
            change_id=config.id,
        )
        return config_id

    def update_onboarding_module_config(
        self,
        deployment_id: str,
        config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        config_id = self.repo.update_onboarding_module_config(
            deployment_id=deployment_id,
            onboarding_module_config=config,
            update_revision=update_revision,
        )
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.ONBOARDING_CONFIG,
            submitter_id=self.submitter_id,
            change_id=config.id,
        )
        return config_id

    def create_article(
        self, deployment_id: str, section_id: str, learn_article: LearnArticle
    ) -> str:
        article_id = self.repo.create_learn_article(
            deployment_id=deployment_id,
            section_id=section_id,
            learn_article=learn_article,
        )
        return article_id

    def create_key_action(self, deployment_id: str, key_action: KeyActionConfig):
        key_action_id = self.repo.create_key_action(
            deployment_id=deployment_id, key_action=key_action
        )
        self._post_key_action_create(deployment_id, key_action_id)
        return key_action_id

    def retrieve_deployments(
        self,
        skip: int = 0,
        limit: int = None,
        search_criteria: str = None,
        sort_fields: list[SortField] = None,
        status: list[Status] = None,
        name_contains: str = None,
    ):
        return self.repo.retrieve_deployments(
            skip, limit, search_criteria, sort_fields, status, name_contains
        )

    def retrieve_deployments_by_ids(
        self, deployment_ids: list[str]
    ) -> list[Deployment]:
        return self.repo.retrieve_deployments_by_ids(deployment_ids=deployment_ids)

    def retrieve_deployment(
        self, deployment_id: str, raise_error=True
    ) -> Optional[Deployment]:
        """Retrieve Deployment from database, and check in case of having licensed questionnaire module load config bodies from
        file system"""

        try:
            deployment = self.repo.retrieve_deployment(deployment_id=deployment_id)
            deployment.load_licensed_config_bodies()
            return deployment
        except DeploymentDoesNotExist as error:
            if not raise_error:
                return
            raise error

    def retrieve_deployment_by_version_number(
        self, deployment_id: str, version_number: int
    ):
        return self.repo.retrieve_deployment_by_version_number(
            deployment_id=deployment_id, version_number=version_number
        )

    def retrieve_deployment_config(self, authz_user: AuthorizedUser) -> Deployment:
        deployment = self.retrieve_deployment(deployment_id=authz_user.deployment_id())
        deployment.managerActivationCode = None
        return deployment.apply_care_plan_by_id(
            authz_user.user.carePlanGroupId, authz_user.id, authz_user.get_role().id
        )

    def retrieve_deployment_with_code(self, code: str) -> tuple[Deployment, str, str]:
        try:
            activation_code = ActivationCode(code)
        except TypeError:
            raise WrongActivationOrMasterKeyException

        return self._retrieve_deployment_with_code(activation_code)

    def _retrieve_deployment_with_code(self, code: ActivationCode):
        deployment = self.repo.retrieve_deployment_by_activation_code(code.base)
        group = deployment.retrieve_care_plan_group_by_code(code.extension)
        if code.extension and not group:
            raise InvalidRequestException

        activation_code_mapping = {
            deployment.userActivationCode: RoleName.USER,
            deployment.managerActivationCode: RoleName.CONTRIBUTOR,
            deployment.proxyActivationCode: RoleName.PROXY,
        }
        role = activation_code_mapping.get(code.base)
        if not role:
            raise InvalidRequestException

        return deployment, role, group.id if group else None

    def retrieve_modules(self) -> list[Module]:
        return inject.instance(ModulesManager).modules

    def retrieve_module(self, module_id: str, primitive: type = None) -> Module:
        def filter_modules(item: Module) -> bool:
            primitive_condition = not primitive or primitive in item.primitives
            return item.moduleId == module_id and primitive_condition

        try:
            return next(filter(filter_modules, self.retrieve_modules()))
        except StopIteration:
            msg = f"Module {module_id} {f'with primitive {primitive.__name__}' if primitive else ''} does not exists."
            raise ModuleWithPrimitiveDoesNotExistException(msg)

    def retrieve_module_configs(
        self, deployment_id: str, module_id: str = None
    ) -> list[ModuleConfig]:
        module_configs = self.repo.retrieve_module_configs(deployment_id=deployment_id)
        if module_id:
            return [mc for mc in module_configs if mc.moduleId == module_id]
        return module_configs

    def check_field_value_exists_in_module_config(
        self, field_path: str, field_value: str
    ) -> bool:
        return self.repo.check_field_value_exists_in_module_configs(
            field_path=field_path, field_value=field_value
        )

    def retrieve_onboarding_module_configs(
        self, deployment_id: str
    ) -> list[OnboardingModuleConfig]:
        return self.repo.retrieve_onboarding_module_configs(deployment_id=deployment_id)

    def retrieve_module_config(self, module_config_id: str) -> Optional[ModuleConfig]:
        return self.repo.retrieve_module_config(module_config_id=module_config_id)

    def retrieve_key_actions(
        self, deployment_id: str, trigger: KeyActionConfig.Trigger
    ):
        return self.repo.retrieve_key_actions(
            deployment_id=deployment_id, trigger=trigger
        )

    def _pre_update_deployment(
        self, deployment: Deployment, previous_state: Deployment
    ):
        event = PreDeploymentUpdateEvent(deployment, previous_state)
        self._event_bus.emit(event, raise_error=True)

    def _post_update_deployment(
        self, deployment: Deployment, previous_state: Deployment
    ):
        event = PostDeploymentUpdateEvent(deployment, previous_state)
        self._event_bus.emit(event, raise_error=True)

    def update_deployment(
        self,
        deployment: Deployment,
        update_revision: bool = True,
        set_update_time: bool = True,
    ) -> str:
        deployment_before_update = self.retrieve_deployment(deployment.id)
        self._pre_update_deployment(deployment, deployment_before_update)

        if set_update_time:
            deployment.updateDateTime = datetime.utcnow()

        if update_revision:
            deployment.version = deployment_before_update.version + 1

        deployment_id = self.repo.update_deployment(deployment)
        self._post_update_deployment(deployment, deployment_before_update)

        if update_revision:
            self.create_deployment_revision(
                deployment=deployment_before_update,
                change_type=ChangeType.DEPLOYMENT,
                submitter_id=self.submitter_id,
                change_id=deployment.id,
            )
        return deployment_id

    def update_enrollment_counter(self, deployment_id, session=None) -> Deployment:
        return self.repo.update_enrollment_counter(
            deployment_id=deployment_id, session=session
        )

    def update_learn_section(
        self, deployment_id: str, learn_section: LearnSection
    ) -> str:
        return self.repo.update_learn_section(
            deployment_id=deployment_id, learn_section=learn_section
        )

    def update_article(
        self, deployment_id: str, section_id: str, article: LearnArticle
    ) -> str:
        article_id = self.repo.update_learn_article(
            deployment_id=deployment_id,
            section_id=section_id,
            article=article,
        )
        return article_id

    def update_key_action(self, deployment_id: str, key_action: KeyActionConfig) -> str:
        key_action_id, updated = self.repo.update_key_action(
            deployment_id=deployment_id,
            key_action_id=key_action.id,
            key_action=key_action,
        )
        if updated:
            self._post_key_action_update(key_action_id, deployment_id)
        return key_action_id

    def delete_deployment(self, deployment_id) -> None:
        self.repo.delete_deployment(deployment_id=deployment_id)
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(DeleteDeploymentEvent(deployment_id))

    def delete_module_config(self, deployment_id: str, module_config_id: str):
        deployment = self.retrieve_deployment(deployment_id)
        self.repo.delete_module_config(
            deployment_id=deployment_id, module_config_id=module_config_id
        )
        self.remove_related_key_actions(module_config_id, deployment)
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.MODULE_CONFIG,
            submitter_id=self.submitter_id,
            change_id=module_config_id,
        )

    def delete_onboarding_module_config(
        self, deployment_id: str, onboarding_config_id: str
    ) -> None:
        deployment = self.retrieve_deployment(deployment_id)
        self.repo.delete_onboarding_module_config(
            deployment_id=deployment_id, onboarding_config_id=onboarding_config_id
        )
        self.create_deployment_revision(
            deployment=deployment,
            change_type=ChangeType.ONBOARDING_CONFIG,
            submitter_id=self.submitter_id,
            change_id=onboarding_config_id,
        )

    def delete_key_action(self, deployment_id: str, key_action_id: str):
        self.repo.delete_key_action(
            deployment_id=deployment_id, key_action_id=key_action_id
        )
        self._post_key_action_delete(key_action_id)

    def is_consent_signed(self, user_id: str, deployment: Deployment) -> bool:
        repo = self.consent_repo
        consent = deployment.latest_consent
        if not consent:
            return True

        log_count = repo.retrieve_log_count(
            consent_id=consent.id,
            revision=consent.revision,
            user_id=user_id,
        )
        return log_count > 0

    def encrypt_value(self, deployment_id: str, value: str) -> str:
        # for now ignoring deployment_id
        secret = self.config.server.deployment.encryptionSecret
        if secret:
            return encrypt(value, secret)
        else:
            raise EncryptionSecretNotAvailable

    def remove_related_key_actions(self, module_config_id: str, deployment: Deployment):
        for key_action in deployment.keyActions or []:
            if key_action.moduleConfigId != module_config_id:
                continue

            self.delete_key_action(deployment.id, key_action.id)

    def create_care_plan_group(
        self, deployment_id: str, request_object: CarePlanGroup
    ) -> bool:
        return self.repo.create_care_plan_group(
            deployment_id=deployment_id, care_plan_group=request_object
        )

    def create_or_update_roles(
        self, deployment_id: str, roles: list[Role]
    ) -> list[str]:
        deployment = self.retrieve_deployment(deployment_id)
        deployment.validate_roles(roles)
        update_role_ids = list(filter(None, [role.id for role in roles]))
        dep_roles = deployment.roles or []
        deleted_ids = [role.id for role in dep_roles if role.id not in update_role_ids]
        updated_ids = self.repo.create_or_update_roles(
            deployment_id=deployment_id, roles=roles
        )
        if deleted_ids:
            self._post_delete_roles_event(deleted_ids, deployment.id)
        return updated_ids

    def retrieve_user_care_plan_group_log(
        self, deployment_id: str, user_id: str
    ) -> list[CarePlanGroupLog]:
        return self.repo.retrieve_user_care_plan_group_log(
            deployment_id=deployment_id, user_id=user_id
        )

    def retrieve_user_notes(self, deployment_id: str, user_id: str) -> list[UserNote]:
        return self.repo.retrieve_user_notes(
            deployment_id=deployment_id, user_id=user_id
        )

    def add_user_observation_note(self, note: UserNote) -> str:
        return self.repo.add_user_observation_note(note)

    def retrieve_user_observation_notes(
        self, deployment_id: str, user_id: str, skip: int, limit: int
    ) -> (list[UserNote], int):
        user_notes, user_notes_count = self.repo.retrieve_user_observation_notes(
            deployment_id=deployment_id, user_id=user_id, skip=skip, limit=limit
        )

        user_ids = {note.submitterId for note in user_notes}
        manager_profiles = AuthorizationService().retrieve_user_profiles_by_ids(
            user_ids
        )
        manager_names = {
            manager.id: manager.get_full_name() for manager in manager_profiles
        }

        for user_note in user_notes:
            user_note.submitterName = manager_names.get(user_note.submitterId)

        return user_notes, user_notes_count

    def create_econsent(self, deployment_id: str, econsent: EConsent) -> str:
        return self.econsent_repo.create_econsent(
            deployment_id=deployment_id, econsent=econsent
        )

    def is_econsent_signed(self, user_id: str, deployment: Deployment) -> bool:
        repo = self.econsent_repo
        econsent = deployment.latest_econsent
        if not econsent:
            return True

        log_count = repo.retrieve_log_count(
            consent_id=econsent.id, revision=econsent.revision, user_id=user_id
        )
        return log_count > 0

    def retrieve_econsent_logs(
        self, econsent_id: str, auth_user: AuthorizedUser, is_for_manager: bool
    ) -> dict:
        user_id = self._get_user_id(auth_user)
        if is_for_manager:
            result = self.econsent_repo.retrieve_signed_econsent_logs(
                econsent_id=econsent_id, user_id=user_id
            )
        else:
            result = self.econsent_repo.retrieve_econsent_pdfs(
                econsent_id=econsent_id, user_id=user_id
            )
            if not result:
                raise EConsentLogDoesNotExist

        return result

    def retrieve_localization(self, deployment_id: str, locale: str) -> dict:
        return self.repo.retrieve_localization(
            deployment_id=deployment_id, locale=locale
        )

    @cached_property
    def _module_ids_with_no_disclaimer_config(self):
        modules_with_no_disclaimer_config = [
            LicensedQuestionnaireModule,
            AwarenessTrainingModule,
            AZScreeningQuestionnaireModule,
            BackgroundInformationModule,
            ECGHealthKitModule,
            HighFrequencyStepModule,
            StepModule,
            SurgeryDetailsModule,
        ]
        excluded_modules = []
        for module in modules_with_no_disclaimer_config:
            excluded_modules.extend(get_all_subclasses(module))
        excluded_module_ids = [
            m.moduleId for m in excluded_modules
        ] + excluded_modules_ids_for_applying_default_disclaimer_config
        return set(excluded_module_ids)

    def apply_default_disclaimer_configs(self, deployment: Deployment):
        if (
            not self.config.server.moduleResult.applyDefaultDisclaimerConfig
            or not deployment.moduleConfigs
        ):
            return
        default_footnote = Footnote.from_dict(
            {
                Footnote.ENABLED: True,
                Footnote.TEXT: LocalizationKeys.DEFAULT_DISCLAIMER_TEXT,
            }
        )
        for module_config in deployment.moduleConfigs:
            if module_config.configBody:
                if module_config.configBody.get("trademarkText"):
                    continue
                if (
                    module_config.configBody.get("questionnaireType")
                    in excluded_questionnaire_types_for_applying_default_disclaimer_config
                ):
                    continue
                if module_config.configBody.get(
                    "isPAM"
                ) or module_config.configBody.get("ispam"):
                    continue
            if module_config.moduleId in self._module_ids_with_no_disclaimer_config:
                continue
            footnote = module_config.footnote
            if not footnote or (not footnote.text and footnote.enabled):
                module_config.footnote = default_footnote

    @staticmethod
    def _get_user_id(auth_user: AuthorizedUser) -> typing.Optional[str]:
        if auth_user.is_user():
            return auth_user.id
        elif auth_user.is_manager():
            return None
        else:
            raise PermissionDenied

    @staticmethod
    def _post_key_action_create(deployment_id: str, key_action_id: str):
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(PostCreateKeyActionConfigEvent(key_action_id, deployment_id))

    @staticmethod
    def _post_key_action_update(key_action_config_id: str, deployment_id: str):
        # TODO make async
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(
            PostUpdateKeyActionConfigEvent(key_action_config_id, deployment_id)
        )

    @staticmethod
    def _post_key_action_delete(key_action_id: str):
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(PostDeleteKeyActionConfigEvent(key_action_id))

    @staticmethod
    def _post_delete_roles_event(deleted_ids: list[str], deployment_id: str):
        event = DeleteDeploymentCustomRolesEvent(deleted_ids, deployment_id)
        event_bus = inject.instance(EventBusAdapter)
        event_bus.emit(event)


class LocalizationKeys:
    DEFAULT_DISCLAIMER_TEXT = "hu_module_config_default_disclaimer_text"
