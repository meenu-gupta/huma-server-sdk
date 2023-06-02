from copy import deepcopy
from dataclasses import field
from datetime import datetime
from enum import Enum

import isodate

from extensions.authorization.models.role.role import RoleName
from extensions.deployment.models.localizable import Localizable
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.models.user_note import UserNote
from extensions.module_result.models.primitives import Questionnaire
from sdk import convertibleclass
from sdk.common.utils import inject
from sdk.common.utils.convertible import required_field, meta, default_field
from sdk.common.utils.validators import (
    validate_duration,
    validate_object_id,
    default_datetime_meta,
    validate_len,
    validate_entity_name,
    not_empty,
    validate_time_durations_in_list,
    remove_duplicates,
    must_not_be_present,
    must_be_at_least_one_of,
)


class TimeOfDay(Enum):
    UPON_WAKING = "UPON_WAKING"
    BEFORE_BREAKFAST = "BEFORE_BREAKFAST"
    AFTER_BREAKFAST = "AFTER_BREAKFAST"
    BEFORE_LUNCH = "BEFORE_LUNCH"
    AFTER_LUNCH = "AFTER_LUNCH"
    BEFORE_DINNER = "BEFORE_DINNER"
    AFTER_DINNER = "AFTER_DINNER"
    BEFORE_BED = "BEFORE_BED"


class Weekday(Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


@convertibleclass
class ModuleSchedule:
    ISO_DURATION = "isoDuration"
    TIMES_PER_DURATION = "timesPerDuration"
    FRIENDLY_TEXT = "friendlyText"
    TIMES_OF_DAY = "timesOfDay"
    TIMES_OF_READINGS = "timesOfReadings"
    SPECIFIC_WEEK_DAYS = "specificWeekDays"

    isoDuration: str = default_field(metadata=meta(validate_duration))
    timesPerDuration: int = default_field(
        metadata=meta(lambda n: int(n) <= 50, value_to_field=int)
    )
    friendlyText: str = default_field(metadata=meta(validate_len(1, 100)))
    timesOfDay: list[TimeOfDay] = default_field()
    timesOfReadings: list[str] = default_field(
        metadata=meta(validate_time_durations_in_list, value_to_field=remove_duplicates)
    )
    specificWeekDays: list[Weekday] = default_field(
        metadata=meta(not_empty, value_to_field=remove_duplicates)
    )

    @classmethod
    def validate(cls, instance):
        custom_message = (
            "Keys should be either "
            "[isoDuration, timesPerDuration, friendlyText, timesOfDay] "
            "or "
            "[isoDuration, timesOfReadings, specificWeekDays]}"
        )
        if instance.timesPerDuration or instance.friendlyText or instance.timesOfDay:
            must_not_be_present(
                custom_message,
                timesOfReadings=instance.timesOfReadings,
                specificWeekDays=instance.specificWeekDays,
            )

    def post_init(self):
        if self.timesOfReadings:
            self.timesOfReadings.sort(
                key=lambda x: isodate.parse_duration(x).total_seconds()
            )
        if self.specificWeekDays:
            weekdays = list(Weekday)
            self.specificWeekDays.sort(key=lambda day: weekdays.index(day))


@convertibleclass
class StaticEvent:
    enabled: bool = required_field()
    isoDuration: str = default_field(metadata=meta(validate_duration))
    title: str = required_field()
    description: str = required_field()


@convertibleclass
class NotificationData(Localizable):
    TITLE = "title"
    BODY = "body"

    title: str = default_field(metadata=meta(validate_entity_name))
    body: str = default_field(metadata=meta(validate_entity_name))

    _localizableFields: tuple[str, ...] = (BODY, TITLE)


@convertibleclass
class Footnote(Localizable):
    ENABLED = "enabled"
    TEXT = "text"

    enabled: bool = field(default=False)
    text: str = default_field()

    _localizableFields: tuple[str, ...] = (TEXT,)


@convertibleclass
class ThresholdRange:
    """
    Threshold range is used to define rules for calculating threshold
    based on given values.
    """

    minValue: float = default_field(metadata=meta(value_to_field=float))
    maxValue: float = default_field(metadata=meta(value_to_field=float))
    exactValueStr: str = default_field()

    @classmethod
    def validate(cls, instance):
        must_be_at_least_one_of(
            exactValueStr=instance.exactValueStr,
            minValue=instance.minValue,
            maxValue=instance.maxValue,
        )
        if instance.exactValueStr:
            must_not_be_present(minValue=instance.minValue, maxValue=instance.maxValue)


class RagThresholdType(Enum):
    VALUE = "VALUE"
    CHANGE_NUMBER = "CHANGE_NUMBER"
    CHANGE_PERCENT = "CHANGE_PERCENT"


@convertibleclass
class RagThreshold(Localizable):
    COLOR = "color"
    DIRECTION = "direction"
    SEVERITY = "severity"
    TYPE = "type"
    FIELD_NAME = "fieldName"
    RANGE = "thresholdRange"
    ENABLED = "enabled"
    # type of threshold. Either VALUE, CHANGE_VALUE or CHANGE_PERCENT.
    # if VALUE compare module result value with threshold range.
    # if CHANGE_VALUE - compare with previous results
    # if CHANGE_PERCENT - compare with previous results in percents
    type: RagThresholdType = required_field()
    # priority of the threshold among other thresholds
    severity: int = required_field(metadata=meta(value_to_field=int))
    # list of rules to compare module result value to. If matched with any rule - give color of current threshold
    thresholdRange: list[ThresholdRange] = required_field(
        metadata=meta(validate_len(min=1))
    )
    color: str = required_field()
    # fieldName is a name of the value field for primitive. For example for Weight module it's "value",
    # for BloodPressure modules it's "systolicValue" or "diastolicValue"
    # for Symptoms it's "complexValues"
    fieldName: str = required_field(metadata=meta(validate_entity_name))
    # enable or disable current threshold
    enabled: bool = required_field()

    _localizableFields: tuple[str, ...] = (FIELD_NAME,)

    def collect_localization_dict_and_replace_original_values(
        self, path: str = "", translation_dict: dict = None
    ) -> dict:
        if translation_dict is None:
            translation_dict = dict()
        translation_placeholder = ""
        for k, v in translation_dict.items():
            if (
                k.startswith("hu_symptom_complexSymptoms")
                and k.endswith("_name")
                and v == self.fieldName
            ):
                translation_placeholder = k
                break
        self.fieldName = translation_placeholder


@convertibleclass
class CustomRagThreshold(RagThreshold):
    IS_CUSTOM = "isCustom"

    isCustom: bool = field(default=True)


@convertibleclass
class ModuleConfig(Localizable):
    ID = "id"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    MODULE_ID = "moduleId"
    MODULE_NAME = "moduleName"
    STATUS = "status"
    CONFIG_BODY = "configBody"
    ABOUT = "about"
    FOOTNOTE = "footnote"
    SCHEDULE = "schedule"
    RAG_THRESHOLDS = "ragThresholds"
    VERSION = "version"
    FIRST_VERSION = 0
    CUSTOM_UNIT = "customUnit"
    CONFIG_BODY_ID = "id"
    LEARN_ARTICLE_IDS = "learnArticleIds"
    NOTIFICATION_DATA = "notificationData"
    SHORT_MODULE_NAME = "shortModuleName"
    ORDER = "order"
    LOCALIZATION_PREFIX = "localizationPrefix"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    moduleId: str = required_field()
    moduleName: str = default_field()  # this could be translation string id
    shortModuleName: str = default_field(metadata=meta(validate_entity_name))
    status: EnableStatus = default_field()
    order: int = field(default=0, metadata=meta(value_to_field=int))
    configBody: dict = default_field()
    about: str = default_field()
    footnote: Footnote = default_field()
    schedule: ModuleSchedule = default_field()
    ragThresholds: list[RagThreshold] = default_field()
    learnArticleIds: list[str] = default_field()
    version: int = field(default=FIRST_VERSION, metadata=meta(value_to_field=int))
    customUnit: str = default_field()
    staticEvent: StaticEvent = default_field()
    notificationData: NotificationData = default_field()
    localizationPrefix: str = default_field()

    _localizableFields: tuple[str, ...] = (ABOUT, FOOTNOTE, NOTIFICATION_DATA)

    def is_enabled(self):
        return self.status == EnableStatus.ENABLED

    def is_observation_note(self) -> bool:
        from extensions.module_result.modules.questionnaire import QuestionnaireModule

        module_type = self.get_config_body().get(QuestionnaireModule.QUESTIONNAIRE_TYPE)
        if module_type == UserNote.UserNoteType.OBSERVATION_NOTES.value:
            return True
        return self.is_for_manager()

    def is_for_manager(self) -> bool:
        return self.get_config_body().get("isForManager", False)

    def is_valid_for(self, role: str):
        if not self.is_enabled():
            return False

        if role == RoleName.USER and self.is_for_manager():
            return False

        if self.is_observation_note() and role == RoleName.PROXY:
            return False

        return True

    def get_config_body(self):
        return self.configBody or {}

    @classmethod
    def validate(cls, instance):
        from extensions.module_result.modules.modules_manager import ModulesManager

        manager = inject.instance(ModulesManager)
        manager.validate_module_config(instance)

    def collect_localization_dict_and_replace_original_values(
        self, path: str = "", translation_dict: dict = None
    ):
        if not self.localizationPrefix:
            self._set_localization_prefix(path)

        if self.configBody:
            self._process_module_config_body(
                self.configBody,
                self.localizationPrefix,
                translation_dict,
            )

        from extensions.module_result.modules import SymptomModule

        if self.moduleId == SymptomModule.moduleId:
            self._localizableFields = (
                self.ABOUT,
                self.NOTIFICATION_DATA,
                self.RAG_THRESHOLDS,
            )

        self.validate(self)
        super().collect_localization_dict_and_replace_original_values(
            self.localizationPrefix, translation_dict
        )

    def is_hybrid_questionnaire(self):
        config_body = self.configBody or {}
        return (
            config_body.get("questionnaireType") == "PAM"
            or config_body.get("isPAM", False)
            or config_body.get("ispam", False)
            or config_body.get("scoreAvailable", False)
        )

    def _set_localization_prefix(self, path: str):
        placeholder = f"hu_{self.moduleId.lower()}"
        if self.moduleId == Questionnaire.__name__:
            if self.moduleName:
                placeholder = f"hu_{self.moduleName.lower()}"
            else:
                placeholder = f"{path}_{self.moduleId.lower()}"

        placeholder = self.sanitize_placeholder(placeholder)
        self.set_field_value(field=self.LOCALIZATION_PREFIX, field_value=placeholder)

    @staticmethod
    def translatable_module_config_paths():
        pages_paths = [
            "name",
            "text",
            "description",
            "items.text",
            "items.shortText",
            "items.placeholder",
            "items.lowerBoundLabel",
            "items.upperBoundLabel",
            "items.options.label",
            "items.autocomplete.placeholder",
            "items.autocomplete.options.value",
            "items.autocomplete.validation.errorMessage",
            "items.fields.placeholder",
            "items.fields.validation.errorMessage",
            "complexSymptoms.scale.value",
            "complexSymptoms.name",
        ]
        pages_paths = [f"pages.{p}" for p in pages_paths]
        fields_to_include = [
            "name",
            "trademarkText",
            "submissionPage.text",
            "submissionPage.buttonText",
        ]
        fields_to_include.extend(pages_paths)
        return fields_to_include

    def _process_module_config_body(
        self, config_body: dict, path: str, translation_dict: dict
    ):
        required_keys = {
            i.split(".")[-1] for i in self.translatable_module_config_paths()
        }
        for key, value in config_body.items():
            if isinstance(value, dict):
                self._process_module_config_body(
                    value, f"{path}_{key}", translation_dict
                )
            elif isinstance(value, list):
                index = 0
                for item in value:
                    if isinstance(item, dict):
                        self._process_module_config_body(
                            item, f"{path}_{key}_{index}", translation_dict
                        )
                    index += 1
            elif isinstance(value, str) and key in required_keys and value:
                if key == "value" and (
                    "autocomplete" not in path and "scale" not in path
                ):
                    continue
                if value.startswith("hu_"):
                    continue
                placeholder = f"{path}_{key}"
                translation_dict[placeholder] = value
                config_body[key] = placeholder


@convertibleclass
class CustomModuleConfig(ModuleConfig):
    REASON = "reason"
    USER_ID = "userId"

    ragThresholds: list[CustomRagThreshold] = default_field()
    reason: str = required_field(metadata=meta(not_empty))
    userId: str = required_field(metadata=meta(validate_object_id, field_to_value=str))
    order: int = default_field()
    version: int = default_field()

    def __str__(self):
        return f"{'configId=' + self.id, 'moduleId' + self.moduleId, 'userId' + self.userId}"


class CustomModuleConfigLogType(Enum):
    RAG = "RAG"
    SCHEDULE = "SCHEDULE"


@convertibleclass
class CustomModuleConfigLog(CustomModuleConfig):
    CLINICIAN_ID = "clinicianId"
    CLINICIAN_NAME = "clinicianName"
    MODULE_CONFIG_ID = "moduleConfigId"
    TYPE = "type"

    clinicianId: str = required_field(metadata=meta(validate_object_id))
    moduleConfigId: str = required_field(metadata=meta(validate_object_id))
    type: CustomModuleConfigLogType = default_field()
    clinicianName: str = default_field()

    REMOVE_FIELD = {
        CustomModuleConfigLogType.RAG: ModuleConfig.SCHEDULE,
        CustomModuleConfigLogType.SCHEDULE: ModuleConfig.RAG_THRESHOLDS,
    }

    @property
    def types(self):
        types = []
        if self.ragThresholds:
            types.append(CustomModuleConfigLogType.RAG)
        if self.schedule:
            types.append(CustomModuleConfigLogType.SCHEDULE)
        return types

    def logs(self, log_type: CustomModuleConfigLogType = None) -> list:
        logs = []
        if log_type is None:
            for each_log_type in self.types:
                log = deepcopy(self)
                log.type = each_log_type
                log.__setattr__(self.REMOVE_FIELD[each_log_type], None)
                logs.append(log)
        elif log_type in self.types:
            log = deepcopy(self)
            log.type = log_type
            log.__setattr__(self.REMOVE_FIELD[log_type], None)
            logs.append(log)
        return logs
