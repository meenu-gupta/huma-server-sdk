from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.common.validators import validate_custom_unit
from extensions.module_result.models.module_config import (
    CustomModuleConfig,
    ModuleConfig, CustomModuleConfigLogType,
)
from sdk.common.utils.convertible import convertibleclass, meta, required_field, positive_integer_field, \
    natural_number_field, default_field
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException
from sdk.common.utils.validators import (
    must_be_present,
    must_not_be_present,
    validate_object_id,
)

DEFAULT_CUSTOM_MODULE_CONFIG_LOG_RESULT_PAGE_SIZE = 20


@convertibleclass
class CustomModuleConfigRequestObject(CustomModuleConfig):
    @classmethod
    def validate(cls, module_config):
        must_not_be_present(
            version=module_config.version,
            updateDateTime=module_config.updateDateTime,
            createDateTime=module_config.createDateTime,
        )

        must_be_present(id=module_config.id, moduleId=module_config.moduleId)
        ModuleConfig.validate(module_config)
        if module_config.customUnit:
            validate_custom_unit(module_config.customUnit)


@convertibleclass
class CreateOrUpdateCustomModuleConfigRequestObject(CustomModuleConfigRequestObject):
    USER = "user"
    CLINICIAN_ID = "clinician_id"

    user: AuthorizedUser = required_field()
    clinician_id: str = required_field(metadata=meta(validate_object_id))

    def check_permissions(self):
        if not self.user.is_user():
            raise PermissionDenied("Feature is not available for non-user roles")

        deployment = self.user.deployment
        old_config = deployment.find_module_config(self.moduleId, self.id)
        if not old_config:
            raise InvalidRequestException(f"Module {self.moduleId}/{self.id} not found")
        self.moduleName = old_config.moduleName if self.moduleName is None else self.moduleName


@convertibleclass
class RetrieveCustomModuleConfigsRequestObject:
    USER_ID = "user_id"

    user_id: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveModuleConfigLogsRequestObject:
    USER_ID = "userId"
    MODULE_CONFIG_ID = "moduleConfigId"
    SKIP = "skip"
    LIMIT = "limit"
    TYPE = "type"

    userId: str = required_field(metadata=meta(validate_object_id))
    moduleConfigId: str = required_field(metadata=meta(validate_object_id))
    skip: int = positive_integer_field(default=None)
    limit: int = natural_number_field(default=None)
    type: CustomModuleConfigLogType = default_field()
