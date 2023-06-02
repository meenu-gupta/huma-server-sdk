from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
)
from extensions.deployment.models.user_note import UserNote
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveUserNotesRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from extensions.module_result.service.module_result_service import ModuleResultService
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.usecase.response_object import Response
from sdk.common.utils.validators import remove_none_values


class RetrieveUserNotesResponse(Response):
    def notes_to_array(self) -> list:
        res = []
        ignore_keys = [CarePlanGroupLog.NOTE, CarePlanGroupLog.FROM_CARE_PLAN_GROUP_ID]

        for note in self.value:
            if note.toCarePlanGroupId:
                res.append(remove_none_values(note.to_dict(), ignore_keys))
            else:
                res.append(remove_none_values(note.to_dict()))
        return res


class RetrieveUserNotesUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        module_result_repo: ModuleResultRepository,
    ):
        self._deployment_repo = deployment_repo
        self._module_result_repo = module_result_repo
        self.deployment_service = DeploymentService(repo=self._deployment_repo)
        self.module_result_service = ModuleResultService(repo=self._module_result_repo)

    def process_request(self, request_object: RetrieveUserNotesRequestObject):
        deployment = self._deployment_repo.retrieve_deployment(
            deployment_id=request_object.deploymentId
        )
        skip = request_object.skip or 0
        limit = request_object.limit or 100

        (
            user_notes,
            user_notes_count,
        ) = self.deployment_service.retrieve_user_observation_notes(
            user_id=request_object.userId,
            deployment_id=request_object.deploymentId,
            skip=skip,
            limit=limit,
        )

        if skip + limit <= user_notes_count:
            return RetrieveUserNotesResponse(value=user_notes)

        skip = max(0, skip - user_notes_count)
        limit = max(0, limit - len(user_notes))

        questionnaire_notes = self.module_result_service.retrieve_observation_notes(
            module_configs=deployment.observation_notes,
            user_id=request_object.userId,
            skip=skip,
            limit=limit,
        )

        care_plan_group_notes = self.deployment_service.retrieve_user_notes(
            user_id=request_object.userId,
            deployment_id=request_object.deploymentId,
        )

        notes: list[UserNote] = user_notes + care_plan_group_notes + questionnaire_notes

        return RetrieveUserNotesResponse(value=notes)
