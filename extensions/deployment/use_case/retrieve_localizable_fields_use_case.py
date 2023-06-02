from extensions.deployment.models.deployment import Deployment, ExtraCustomFieldConfig
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    RetrieveLocalizableFieldsRequestObject,
)
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.modules import SymptomModule
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveLocalizableFieldsUseCase(UseCase):
    @autoparams()
    def __init__(self, deployment_repo: DeploymentRepository):
        self._deployment_repo = deployment_repo

    def process_request(self, request_object: RetrieveLocalizableFieldsRequestObject):
        default_path = "deployment"
        deployment = self._deployment_repo.retrieve_deployment(
            deployment_id=request_object.deploymentId
        )
        res = deployment.get_localized_path(path=default_path)
        if extra_custom_fields := deployment.extraCustomFields:
            res.extend(self._generate_extra_custom_fields_paths(extra_custom_fields))

        if module_configs := deployment.moduleConfigs:
            res.extend(self._generate_modules_config_body_paths())

            module_ids = {i.moduleId for i in module_configs}
            if SymptomModule.moduleId in module_ids:
                res.append(
                    f"{default_path}.{SymptomModule.moduleId.lower()}.ragThresholds.fieldName"
                )

        return Response(res)

    @staticmethod
    def _generate_extra_custom_fields_paths(extra_custom_fields: dict) -> list[str]:
        fields_to_include = [
            ExtraCustomFieldConfig.ERROR_MESSAGE,
            ExtraCustomFieldConfig.ONBOARDING_COLLECTION_TEXT,
            ExtraCustomFieldConfig.PROFILE_COLLECTION_TEXT,
        ]
        extra_fields_res = []

        for field_name in extra_custom_fields:
            fields_paths = [
                f"{Deployment.__name__.lower()}.{Deployment.EXTRA_CUSTOM_FIELDS}.{field_name}.{i}"
                for i in fields_to_include
            ]
            extra_fields_res.extend(fields_paths)

        return extra_fields_res

    @staticmethod
    def _generate_modules_config_body_paths() -> list[str]:
        main_path = f"{Deployment.__name__.lower()}.{Deployment.MODULE_CONFIGS}.{ModuleConfig.CONFIG_BODY}"
        translatable_paths = ModuleConfig.translatable_module_config_paths()
        return [f"{main_path}.{p}" for p in translatable_paths]
