from extensions.deployment.router.deployment_requests import DeleteArticleRequestObject
from extensions.deployment.use_case.delete_learn_use_case import DeleteLearnUseCase


class DeleteLearnArticleUseCase(DeleteLearnUseCase):
    def process_request(self, request_object: DeleteArticleRequestObject):
        deployment = self.retrieve_deployment(deployment_id=request_object.deploymentId)
        self._repo.delete_learn_article(
            deployment_id=request_object.deploymentId,
            section_id=request_object.sectionId,
            article_id=request_object.articleId,
        )
        self.remove_article_dependencies(
            request_object.articleId, deployment, request_object.userId
        )
