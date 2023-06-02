from datetime import datetime

from extensions.module_result.models.module_config import (
    CustomModuleConfig,
    CustomModuleConfigLog,
    CustomModuleConfigLogType,
)
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.module_result.repository.models.mongo_custom_module_config_log_model import (
    MongoCustomModuleConfigLog,
)
from extensions.module_result.repository.models.mongo_custom_module_config_model import (
    MongoCustomModuleConfig,
)


class MongoCustomModuleConfigRepository(CustomModuleConfigRepository):
    def create_or_update_custom_module_config(
        self,
        module_config_id: str,
        module_config: CustomModuleConfig,
        user_id: str,
        clinician_id: str,
    ) -> str:
        custom_config = MongoCustomModuleConfig.objects(
            id=module_config_id, userId=user_id
        ).first()

        if not custom_config:
            module_config.createDateTime = module_config.updateDateTime = datetime.now()
            custom_config = MongoCustomModuleConfig(
                **module_config.to_dict(include_none=False)
            )
            custom_config.save()
        else:
            module_config.updateDateTime = datetime.now()
            config = module_config.to_dict(include_none=False)
            custom_config.update(**config)

        self._create_custom_module_config_log(module_config, clinician_id)
        return str(custom_config.id)

    @staticmethod
    def _create_custom_module_config_log(
        module_config: CustomModuleConfig, clinician_id: str
    ):
        module_config_dict = module_config.to_dict(include_none=False)
        module_config_dict.pop(CustomModuleConfig.ID)
        log = CustomModuleConfigLog.from_dict(
            {
                **module_config_dict,
                CustomModuleConfigLog.CLINICIAN_ID: clinician_id,
                CustomModuleConfigLog.MODULE_CONFIG_ID: module_config.id,
            }
        )
        log.createDateTime = log.updateDateTime = datetime.now()
        log_obj = MongoCustomModuleConfigLog(**log.to_dict(include_none=False))
        log_obj.save()

    def retrieve_custom_module_configs(self, user_id: str) -> list[str]:
        configs = MongoCustomModuleConfig.objects(userId=user_id)
        return [CustomModuleConfig.from_dict(config.to_dict()) for config in configs]

    def retrieve_custom_module_config_logs(
        self,
        user_id: str,
        module_config_id: str,
        log_type: CustomModuleConfigLogType,
        skip: int = None,
        limit: int = None,
    ) -> (list[CustomModuleConfigLog], int):
        results = MongoCustomModuleConfigLog.objects(
            userId=user_id, moduleConfigId=module_config_id
        )

        logs = []
        for log in results:
            log_obj = CustomModuleConfigLog.from_dict(log.to_dict())
            logs.extend(log_obj.logs(log_type))
        total = len(logs)
        if skip:
            logs = logs[skip:]
        if limit:
            logs = logs[:limit]
        return logs, total
