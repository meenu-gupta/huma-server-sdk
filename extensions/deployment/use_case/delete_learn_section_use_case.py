from extensions.deployment.router.deployment_requests import (
    DeleteLearnSectionRequestObject,
)
from extensions.deployment.use_case.delete_learn_use_case import DeleteLearnUseCase


class DeleteLearnSectionUseCase(DeleteLearnUseCase):
    """
    Removes learn section with all included articles from deployment.
    Remove/clear deployment from traces/dependencies of removed objects.
    """

    def process_request(self, request_object: DeleteLearnSectionRequestObject):
        deployment_id = request_object.deploymentId
        section_id = request_object.sectionId
        user_id = request_object.userId
        deployment = self.retrieve_deployment(deployment_id=deployment_id)
        self._repo.delete_learn_section(
            deployment_id=deployment_id,
            section_id=section_id,
        )
        self.remove_section_dependencies(section_id, deployment, user_id)
