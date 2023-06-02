from extensions.authorization.services.authorization import AuthorizationService
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.router.custom_module_config_requests import (
    RetrieveModuleConfigLogsRequestObject,
)
from extensions.module_result.router.module_result_response import (
    CustomModuleConfigLogResponseObject,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveModuleConfigLogsUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: CustomModuleConfigRepository):
        self._repo = repo

    def process_request(
        self, request_object: RetrieveModuleConfigLogsRequestObject
    ) -> CustomModuleConfigLogResponseObject:
        logs, total = self._repo.retrieve_custom_module_config_logs(
            user_id=request_object.userId,
            module_config_id=request_object.moduleConfigId,
            log_type=request_object.type,
            skip=request_object.skip,
            limit=request_object.limit,
        )
        self._add_clinician_names(logs)
        return CustomModuleConfigLogResponseObject(logs=logs, total=total)

    @staticmethod
    def _add_clinician_names(logs):
        user_names = {}
        for log in logs:
            if user_names.get(log.clinicianId) is None:
                user = AuthorizationService().retrieve_simple_user_profile(
                    log.clinicianId
                )
                user_names[log.clinicianId] = user.get_full_name()
            log.clinicianName = user_names[log.clinicianId]
