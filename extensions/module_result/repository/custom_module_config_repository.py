import abc

from extensions.module_result.models.module_config import (
    CustomModuleConfig,
    CustomModuleConfigLog,
    CustomModuleConfigLogType,
)


class CustomModuleConfigRepository(abc.ABC):
    @abc.abstractmethod
    def create_or_update_custom_module_config(
        self,
        module_config_id: str,
        module_config: CustomModuleConfig,
        user_id: str,
        clinician_id: str,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_custom_module_configs(self, user_id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_custom_module_config_logs(
        self,
        user_id: str,
        module_config_id: str,
        log_type: CustomModuleConfigLogType,
        skip: int = None,
        limit: int = None,
    ) -> (list[CustomModuleConfigLog], int):
        raise NotImplementedError
