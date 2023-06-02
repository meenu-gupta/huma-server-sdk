from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    ReorderRequestObject,
    ReorderLearnArticles,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class ReorderUseCase(UseCase):
    @autoparams()
    def __init__(self, deployment_repo: DeploymentRepository):
        self._deployment_repo = deployment_repo

    def process_request(self, request_object: ReorderRequestObject):
        raise NotImplementedError


class ReorderOnboardingModuleConfigsUseCase(ReorderUseCase):
    def process_request(self, request_object: ReorderRequestObject):
        self._deployment_repo.reorder_onboarding_module_configs(
            deployment_id=request_object.deploymentId,
            ordering_data=request_object.items,
        )
        return [o.id for o in request_object.items]


class ReorderModuleConfigsUseCase(ReorderUseCase):
    def process_request(self, request_object: ReorderRequestObject):
        self._deployment_repo.reorder_module_configs(
            deployment_id=request_object.deploymentId,
            ordering_data=request_object.items,
        )
        return [m.id for m in request_object.items]


class ReorderLearnSectionsUseCase(ReorderUseCase):
    def process_request(self, request_object: ReorderRequestObject):
        self._deployment_repo.reorder_learn_sections(
            deployment_id=request_object.deploymentId,
            ordering_data=request_object.items,
        )
        return [s.id for s in request_object.items]


class ReorderLearnArticlesUseCase(ReorderUseCase):
    def process_request(self, request_object: ReorderLearnArticles):
        self._deployment_repo.reorder_learn_articles(
            deployment_id=request_object.deploymentId,
            ordering_data=request_object.items,
            section_id=request_object.sectionId,
        )

        return [a.id for a in request_object.items]
