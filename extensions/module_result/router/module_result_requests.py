import logging
from copy import deepcopy
from datetime import datetime

from extensions.authorization.models.user import User
from extensions.common.sort import SortField
from extensions.deployment.models.deployment import Deployment
from extensions.exceptions import ValidationDataError
from extensions.module_result.common.questionnaire_utils import (
    build_question_map,
    manual_translation,
)
from extensions.module_result.exceptions import InvalidModuleConfiguration
from extensions.module_result.models.primitives import Primitive, Questionnaire
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.modules_manager import ModulesManager
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.convertible import (
    convertibleclass,
    ConvertibleClassValidationError,
    required_field,
    positive_integer_field,
    meta,
    default_field,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import (
    utc_str_field_to_val,
    utc_str_val_to_field,
    default_datetime_meta,
    validate_language,
    validate_timezone,
    validate_object_id,
)

logger = logging.getLogger(__name__)


@convertibleclass
class CreateModuleResultRequestObject(RequestObject):
    RAW_DATA = "rawData"
    USER = "user"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"
    DEPLOYMENT = "deployment"
    LANGUAGE = "language"

    deployment: Deployment = required_field()
    moduleId: str = required_field()
    rawData: list[dict] = required_field()
    primitives: list[Primitive] = default_field()
    user: User = required_field()
    module: Module = default_field()
    moduleConfigId: str = default_field()
    language: str = default_field(metadata=meta(validate_language))

    errors: list[str] = default_field(metadata=meta(value_to_field=lambda: []))

    def post_init(self):
        self.primitives, _ = self._build_module_result(self.rawData)
        self.module = self._get_module()
        module_config = self.module.extract_module_config(
            self.deployment.moduleConfigs, self.primitives[0], self.moduleConfigId
        )
        self.module.config = module_config
        translated_data = self._apply_localization(self.rawData)
        self.primitives, self.errors = self._build_module_result(translated_data)
        for primitive in self.primitives:
            primitive.moduleConfigId = module_config.id
        self.moduleConfigId = module_config.id

    @classmethod
    def validate(cls, req_obj):
        for primitive in req_obj.rawData:
            if not primitive.get("type"):
                raise ValidationDataError("Field [type] must be present in primitive.")

    def _apply_localization(self, raw_data: list[dict]):
        if isinstance(self.module, LicensedQuestionnaireModule):
            localization = self.deployment.get_localization(self.language)
        else:
            localization = self.deployment.get_localization(
                self.language, include_licensed=False
            )

        if prefix := self.module.config.localizationPrefix:
            localization = {
                key: value
                for key, value in localization.items()
                if key.startswith(prefix)
            }

        reverse_localization = {val: key for key, val in localization.items()}
        questionnaire = find(lambda p: isinstance(p, Questionnaire), self.primitives)
        if questionnaire:
            question_map = build_question_map(self.module.config.configBody)
            raw_data = manual_translation(raw_data, question_map, localization)

        ignored_keys = set(Primitive.__annotations__.keys()) | {
            Questionnaire.QUESTIONNAIRE_NAME,
            "type",
        }

        return replace_values(
            raw_data,
            reverse_localization,
            check_hashable=False,
            string_list_translator=self.module.usesListStringTranslation,
            ignored_keys=ignored_keys,
        )

    @autoparams("manager")
    def _get_module(self, manager: ModulesManager):
        module = manager.find_module(self.moduleId, {type(p) for p in self.primitives})
        if not module:
            raise InvalidModuleConfiguration(f"Module {self.module} is not configured.")
        return deepcopy(module)

    @staticmethod
    def _build_module_result(
        primitive_dicts: list[dict],
    ) -> tuple[list[Primitive], list[str]]:
        """
        Convert all primitives in primitive_dict_list from dict to primitive instance.
        If conversion is not possible, add primitive name to error list.
        @param primitive_dicts: list of primitive dicts to convert from.
        @return: (list[Primitive], list[str]) - tuple of primitives and list of primitive names that can't be converted.
        """
        primitives = []
        errors = []
        for primitive_dict in primitive_dicts:
            primitive_type = primitive_dict["type"]
            try:
                primitive = Primitive.create_from_dict(primitive_dict, primitive_type)
            except Exception as error:
                err_message = (
                    f"Error building primitive from {primitive_dict}: {error}."
                )
                logger.warning(err_message)
                errors.append(err_message)
            else:
                primitives.append(primitive)

        if not primitives:
            msg = f"All primitives failed validation: {', '.join(errors)}"
            raise InvalidRequestException(msg)

        return primitives, errors


@convertibleclass
class BaseRetrieveModuleResultRequestObject:
    """
    - direction always refer to startDateTime
    - it's either skip + limit or fromDateTime + toDateTime
    """

    SKIP = "skip"
    LIMIT = "limit"
    DIRECTION = "direction"
    FROM_DATE_TIME = "fromDateTime"
    TO_DATE_TIME = "toDateTime"
    FILTERS = "filters"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    ROLE = "role"

    skip: int = positive_integer_field(default=None)
    limit: int = positive_integer_field(default=None)
    direction: SortField.Direction = default_field()
    fromDateTime: datetime = default_field(metadata=default_datetime_meta())
    toDateTime: datetime = default_field(metadata=default_datetime_meta())
    filters: dict = default_field()
    userId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))
    role: str = required_field()


@convertibleclass
class RetrieveModuleResultsRequestObject(BaseRetrieveModuleResultRequestObject):
    EXCLUDED_FIELDS = "excludedFields"
    MODULE_CONFIG_ID = "moduleConfigId"
    MODULE_ID = "moduleId"
    NORMAL_QUESTIONNAIRES = "normalQuestionnaires"
    EXCLUDE_MODULE_IDS = "excludeModuleIds"
    UNSEEN_ONLY = "unseenOnly"

    moduleId: str = required_field()
    moduleConfigId: str = default_field(metadata=meta(validate_object_id))
    excludedFields: list[str] = default_field()
    normalQuestionnaires: bool = default_field()
    excludeModuleIds: list[str] = default_field()
    unseenOnly: bool = default_field()


@convertibleclass
class RetrieveModuleResultRequestObject:
    MODULE_RESULT_ID = "moduleResultId"
    PRIMITIVE_TYPE = "primitiveType"
    USER_ID = "userId"

    userId: str = required_field(metadata=meta(validate_object_id))
    moduleResultId: str = required_field(metadata=meta(validate_object_id))
    primitiveType: str = required_field()


@convertibleclass
class SearchModuleResultsRequestObject(BaseRetrieveModuleResultRequestObject):
    MODULES = "modules"

    modules: list[str] = required_field()


@convertibleclass
class AggregateModuleResultsRequestObjects:
    USER_ID = "userId"
    MODE = "mode"
    PRIMITIVE_NAME = "primitiveName"
    FUNCTION = "function"
    FROM_DATE = "fromDateTime"
    TO_DATE = "toDateTime"
    SKIP = "skip"
    LIMIT = "limit"
    TIMEZONE = "timezone"

    function: AggregateFunc = required_field()
    primitiveName: str = required_field()
    mode: AggregateMode = required_field()
    fromDateTime: datetime = required_field(
        metadata=meta(
            field_to_value=utc_str_field_to_val,
            value_to_field=utc_str_val_to_field,
        ),
    )
    toDateTime: datetime = required_field(
        metadata=meta(
            field_to_value=utc_str_field_to_val,
            value_to_field=utc_str_val_to_field,
        ),
    )

    skip: int = positive_integer_field(default=None)
    limit: int = positive_integer_field(default=None)
    userId: str = default_field(metadata=meta(validate_object_id))
    timezone: str = default_field(metadata=meta(validate_timezone))
    moduleConfigId: str = default_field()

    @classmethod
    def validate(cls, instance):
        primitive_cls = Primitive.get_class(instance.primitiveName)
        if instance.function not in primitive_cls.ALLOWED_AGGREGATE_FUNCS:
            raise ConvertibleClassValidationError(
                f'Function "{instance.function}" is not allowed for this module'
            )


@convertibleclass
class RetrieveUnseenModuleResultRequestObject:
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    HYBRID_QUESTIONNAIRE_MODULE_IDS = "hybridQuestionnaireModuleIds"
    ENABLED_MODULE_IDS = "enabledModuleIds"

    userId: str = default_field(metadata=meta(validate_object_id))
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    hybridQuestionnaireModuleIds: list[str] = default_field()
    enabledModuleIds: list[str] = default_field()
