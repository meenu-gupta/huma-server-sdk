from abc import ABC, abstractmethod
from typing import Optional

from extensions.authorization.models.role.role import Role
from extensions.common.sort import SortField
from extensions.deployment.models.care_plan_group import CarePlanGroup, CarePlanGroupLog
from extensions.deployment.models.deployment import (
    Deployment,
    Label,
    ModuleConfig,
    OnboardingModuleConfig,
    DeploymentRevision,
    DeploymentTemplate,
)
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import (
    LearnArticle,
    LearnSection,
    OrderUpdateObject,
)
from extensions.deployment.models.status import Status
from extensions.deployment.models.user_note import UserNote


class DeploymentRepository(ABC):
    session = None
    IGNORED_FIELDS = ()

    @abstractmethod
    def start_transaction(self):
        raise NotImplementedError

    @abstractmethod
    def commit_transactions(self):
        raise NotImplementedError

    @abstractmethod
    def cancel_transactions(self):
        raise NotImplementedError

    @abstractmethod
    def create_deployment(self, deployment: Deployment) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_module_config(
        self, deployment_id: str, config: ModuleConfig, update_revision: bool = True
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_module_config(
        self,
        deployment_id: str,
        config: ModuleConfig,
        update_revision: bool = True,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_onboarding_module_config(
        self,
        deployment_id: str,
        onboarding_module_config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_deployment_revision(self, deployment_revision: DeploymentRevision):
        raise NotImplementedError

    @abstractmethod
    def create_onboarding_module_config(
        self,
        deployment_id: str,
        config: OnboardingModuleConfig,
        update_revision: bool = True,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_key_action(
        self,
        deployment_id: str,
        key_action: KeyActionConfig,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_learn_section(
        self, deployment_id: str, learn_section: LearnSection
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_learn_article(
        self, deployment_id: str, section_id: str, learn_article: LearnArticle
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment(self, deployment_id: str) -> Deployment:
        raise NotImplementedError

    @abstractmethod
    def update_enrollment_counter(self, deployment_id: str, **kwargs) -> Deployment:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_by_version_number(
        self, deployment_id: str, version_number: int
    ) -> Deployment:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_revisions(
        self, deployment_id: str
    ) -> list[DeploymentRevision]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployments(
        self,
        skip: int = None,
        limit: int = None,
        search_criteria: str = None,
        sort_fields: list[SortField] = None,
        status: list[Status] = None,
        name_contains: str = None,
    ) -> tuple[list[Deployment], int]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployments_by_ids(
        self, deployment_ids: list[str]
    ) -> list[Deployment]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_codes(self, deployment_ids: list[str]) -> dict:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_by_activation_code(
        self, deployment_code: str
    ) -> Deployment:
        raise NotImplementedError

    @abstractmethod
    def retrieve_module_configs(self, deployment_id: str) -> list[ModuleConfig]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_module_config(self, module_config_id: str) -> Optional[ModuleConfig]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_key_actions(
        self, deployment_id: str, trigger: KeyActionConfig.Trigger = None
    ):
        raise NotImplementedError

    @abstractmethod
    def update_deployment(self, deployment: Deployment) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_labels(self, deployment_id: str) -> list[Label]:
        raise NotImplementedError

    @abstractmethod
    def create_deployment_labels(self, deployment_id, labels: list[Label]):
        raise NotImplementedError

    @abstractmethod
    def update_deployment_labels(
        self, deployment_id, labels: list[Label], updated_label: Optional[Label]
    ):
        raise NotImplementedError

    @abstractmethod
    def delete_deployment_label(self, deployment_id, label_id):
        raise NotImplementedError

    @abstractmethod
    def update_learn_article(
        self,
        deployment_id: str,
        section_id: str,
        article: LearnArticle,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_learn_section(
        self,
        deployment_id: str,
        learn_section: LearnSection,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def reorder_learn_sections(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):
        raise NotImplementedError

    @abstractmethod
    def reorder_learn_articles(
        self,
        deployment_id: str,
        section_id: str,
        ordering_data: list[OrderUpdateObject],
    ):
        raise NotImplementedError

    @abstractmethod
    def reorder_module_configs(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):
        raise NotImplementedError

    @abstractmethod
    def reorder_onboarding_module_configs(
        self, deployment_id: str, ordering_data: list[OrderUpdateObject]
    ):
        raise NotImplementedError

    @abstractmethod
    def update_key_action(
        self,
        deployment_id: str,
        key_action_id: str,
        key_action: KeyActionConfig,
    ) -> tuple[str, bool]:
        raise NotImplementedError

    @abstractmethod
    def delete_deployment(self, deployment_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_module_config(self, deployment_id: str, module_config_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_onboarding_module_config(
        self, deployment_id: str, onboarding_config_id: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_learn_section(self, deployment_id: str, section_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_learn_article(
        self, deployment_id: str, section_id: str, article_id: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_key_action(self, deployment_id: str, key_action_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_care_plan_group(
        self, deployment_id: str, care_plan_group: CarePlanGroup
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_or_update_roles(
        self,
        deployment_id: str,
        roles: list[Role],
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_user_care_plan_group_log(
        self, deployment_id: str, user_id: str
    ) -> list[CarePlanGroupLog]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_user_notes(self, deployment_id: str, user_id: str) -> list[UserNote]:
        raise NotImplementedError

    @abstractmethod
    def add_user_observation_note(self, user_note: UserNote) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_user_observation_notes(
        self, deployment_id: str, user_id: str, skip: int = 0, limit: int = 100
    ) -> (list[UserNote], int):
        raise NotImplementedError

    @abstractmethod
    def update_localizations(self, deployment_id: str, localizations: dict) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_localization(self, deployment_id: str, locale: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def retrieve_onboarding_module_configs(
        self, deployment_id: str
    ) -> list[OnboardingModuleConfig]:
        raise NotImplementedError

    def retrieve_deployment_revision_by_module_config_version(
        self,
        deployment_id: str,
        module_id: str,
        module_config_version: int,
        module_config_id: str = None,
        config_body_id: str = None,
    ) -> Optional[DeploymentRevision]:
        raise NotImplementedError

    @abstractmethod
    def check_field_value_exists_in_module_configs(
        self, field_path: str, field_value: str
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def update_full_deployment(self, deployment: Deployment) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_deployment_template(self, template: DeploymentTemplate) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_templates(
        self, organization_id: str = None
    ) -> list[DeploymentTemplate]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_deployment_template(self, template_id: str) -> DeploymentTemplate:
        raise NotImplementedError

    @abstractmethod
    def update_deployment_template(
        self, template_id: str, template: DeploymentTemplate
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_deployment_template(self, template_id: str):
        raise NotImplementedError

    @abstractmethod
    def retrieve_files_in_library(
        self,
        library_id: str,
        deployment_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ):
        raise NotImplementedError
