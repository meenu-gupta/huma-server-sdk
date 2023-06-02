from extensions.deployment.models.user_note import UserNote
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import AddUserNotesRequestObject
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.service.module_result_service import ModuleResultService
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class AddUserNotesUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        module_results_repo: ModuleResultRepository,
    ):
        self._deployment_repo = deployment_repo
        self.deployment_service = DeploymentService(repo=self._deployment_repo)
        self.module_results_repo = module_results_repo
        self.module_result_service = ModuleResultService(repo=self.module_results_repo)

    def process_request(self, request_object: AddUserNotesRequestObject):
        request_dict = request_object.to_dict()
        note = UserNote.from_dict(
            {
                **request_dict,
                UserNote.TYPE: UserNote.UserNoteType.USER_OBSERVATION_NOTES.value,
            }
        )
        inserted_note_id = self.deployment_service.add_user_observation_note(note)
        self.module_results_repo.flush_unseen_results(
            user_id=request_object.userId,
            start_date_time=request_object.createDateTime,
        )
        self.module_result_service.update_unseen_flags(request_object.userId)
        return {"id": inserted_note_id}
