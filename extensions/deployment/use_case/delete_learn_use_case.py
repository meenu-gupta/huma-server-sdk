from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.service.deployment_service import DeploymentService
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class DeleteLearnUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: DeploymentRepository):
        self._repo = repo
        # TODO when key action service methods will be moved to use case - change this logic
        self.service = DeploymentService(repo=self._repo)

    def process_request(self, request_object):
        raise NotImplementedError

    def retrieve_deployment(self, deployment_id):
        return self._repo.retrieve_deployment(deployment_id=deployment_id)

    def remove_section_dependencies(
        self, section_id: str, deployment: Deployment, user_id: str
    ):
        section = self.find_section_by_id(section_id, deployment)
        for article in section.articles or []:
            self.remove_article_dependencies(article.id, deployment, user_id)

    def remove_article_dependencies(
        self, article_id: str, deployment: Deployment, user_id: str
    ):
        self.remove_related_key_actions(article_id, deployment)
        self.clear_related_module_configs(article_id, deployment, user_id)

    def remove_related_key_actions(self, article_id: str, deployment: Deployment):
        for key_action in deployment.keyActions or []:
            if key_action.learnArticleId == article_id:
                self.service.delete_key_action(
                    deployment_id=deployment.id, key_action_id=key_action.id
                )

    def clear_related_module_configs(
        self, article_id: str, deployment: Deployment, user_id: str
    ):
        for module_config in deployment.moduleConfigs or []:
            if article_id in (module_config.learnArticleIds or []):
                module_config.learnArticleIds.remove(article_id)
                self.service.create_or_update_module_config(
                    deployment_id=deployment.id, config=module_config
                )

    @staticmethod
    def find_section_by_id(section_id: str, deployment: Deployment):
        matched_sections = filter(
            lambda section: section.id == section_id, deployment.learn.sections or []
        )
        try:
            return next(matched_sections)
        except StopIteration:
            raise ObjectDoesNotExist
