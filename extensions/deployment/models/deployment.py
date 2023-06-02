"""model for deployment"""
import copy
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Optional

import isodate
from tomlkit._utils import merge_dicts

from extensions.authorization.models.role.role import (
    CustomRolesExtension,
    Role,
    RoleName,
)
from extensions.authorization.models.user import User
from extensions.common.legal_documents import LegalDocument
from extensions.common.s3object import S3Object
from extensions.dashboard.models.configuration import DeploymentLevelConfiguration
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroup,
    CarePlanGroupDeploymentExtension,
)
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import Learn
from extensions.deployment.models.localizable import Localizable
from extensions.deployment.models.stats import DeploymentStats
from extensions.deployment.models.status import Status, EnableStatus
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from extensions.module_result.exceptions import InvalidModuleConfiguration
from extensions.module_result.models.module_config import (
    CustomModuleConfig,
    ModuleConfig,
)
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.localization.utils import Language, Localization
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    ConvertibleClassValidationError,
    required_field,
    url_field,
    default_field,
    dict_field,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    validate_color,
    validate_activation_code,
    validate_object_id,
    validate_duration,
    default_datetime_meta,
    validate_entity_name,
    validate_len,
    validate_range,
    validate_regex,
    incorrect_language_to_default,
    remove_duplicates,
    not_empty,
    validate_country,
    str_id_to_obj_id,
    must_not_be_present,
    validate_object_ids,
    validate_no_duplicate_keys_value_in_list,
    read_json_file,
    validate_country_code,
)


@autoparams("repo")
def fetch_custom_module_configs_of_user(
    user_id: str, repo: CustomModuleConfigRepository
):
    return repo.retrieve_custom_module_configs(user_id=user_id)


@convertibleclass
class OnboardingModuleConfig:
    ID = "id"
    ONBOARDING_ID = "onboardingId"
    STATUS = "status"
    CONFIG_BODY = "configBody"
    ORDER = "order"
    VERSION = "version"
    USER_TYPES = "userTypes"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    onboardingId: str = required_field()
    status: EnableStatus = default_field()
    configBody: dict = default_field()
    order: int = required_field(metadata=meta(value_to_field=int))
    version: int = field(default=0, metadata=meta(value_to_field=int))
    userTypes: list[str] = field(
        default_factory=lambda: ["User"], metadata=meta(validate_len(1))
    )

    def get_config_body(self):
        return self.configBody or {}

    def is_enabled(self):
        return self.status == EnableStatus.ENABLED

    def is_valid_for(self, role_type: str):
        return role_type in self.userTypes

    @classmethod
    def validate(cls, instance):
        for user_type in instance.userTypes:
            if not Role.UserType.validate(user_type):
                raise ConvertibleClassValidationError


@convertibleclass
class Label:

    ID = "id"
    TEXT = "text"
    AUTHOR_ID = "authorId"
    CREATE_DATE_TIME = "createDateTime"
    UPDATED_BY = "updatedBy"
    UPDATE_DATE_TIME = "updateDatetime"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    text: str = default_field()
    authorId: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    createDateTime: datetime = default_field(
        metadata=default_datetime_meta(), default=datetime.now()
    )
    updatedBy: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class ProfileExtraIds:
    ALIVE_COR_ID = "aliveCorId"
    FENLAND_COHORT_ID = "fenlandCohortId"
    INSURANCE_NUMBER = "insuranceNumber"
    NHS_ID = "nhsId"
    WECHAT_ID = "wechatId"

    USER_FIELDS = (
        FENLAND_COHORT_ID,
        NHS_ID,
        INSURANCE_NUMBER,
        WECHAT_ID,
        ALIVE_COR_ID,
    )

    fenlandCohortId: bool = field(default=False)
    nhsId: bool = field(default=False)
    insuranceNumber: bool = field(default=False)
    wechatId: bool = field(default=False)
    aliveCorId: bool = field(default=False)

    mandatoryOnboardingIds: list[str] = default_field()
    unEditableIds: list[str] = default_field()

    @classmethod
    def validate(cls, instance: "ProfileExtraIds"):
        if not instance.unEditableIds:
            return
        for id_ in instance.unEditableIds:
            if id_ not in cls.USER_FIELDS:
                msg = f"Field [{id_}] in [unEditableIds] is not supported."
                raise ConvertibleClassValidationError(msg)


@convertibleclass
class GenderOptionType(Localizable):
    DISPLAY_NAME = "displayName"

    displayName: str = required_field(metadata=meta(validate_entity_name))
    value: str = required_field()

    _localizableFields: tuple[str, ...] = (DISPLAY_NAME,)


@convertibleclass
class AdditionalContactDetailsItem:
    ALT_CONTACT_NUMBER = "altContactNumber"
    REGULAR_CONTACT_NAME = "regularContactName"
    REGULAR_CONTACT_NUMBER = "regularContactNumber"
    EMERGENCY_CONTACT_NAME = "emergencyContactName"
    EMERGENCY_CONTACT_NUMBER = "emergencyContactNumber"
    MANDATORY_FIELDS = "mandatoryFields"

    altContactNumber: bool = field(default=True)
    regularContactName: bool = field(default=True)
    regularContactNumber: bool = field(default=True)
    emergencyContactName: bool = field(default=True)
    emergencyContactNumber: bool = field(default=True)
    mandatoryFields: list[str] = default_field()

    @classmethod
    def validate(cls, instance):
        instance_dict = instance.to_dict(include_none=False)
        mandatory_fields = instance.mandatoryFields or []
        for key, value in instance_dict.items():
            if not value and key in mandatory_fields:
                error_message = (
                    f"{key} should not be in mandatoryFields list if it is not required"
                )
                raise ConvertibleClassValidationError(error_message)


@convertibleclass
class EthnicityOption(Localizable):
    DISPLAY_NAME = "displayName"
    VALUE = "value"

    displayName: str = required_field(metadata=meta(validate_entity_name))
    value: str = required_field()

    _localizableFields: tuple[str, ...] = (DISPLAY_NAME,)


@convertibleclass
class FieldValidator:
    MIN = "min"
    MAX = "max"
    MIN_ISO_DURATION = "minISODuration"
    MAX_ISO_DURATION = "maxISODuration"

    min: datetime = default_field(metadata=default_datetime_meta())
    max: datetime = default_field(metadata=default_datetime_meta())
    minISODuration: str = default_field(metadata=meta(validate_duration))
    maxISODuration: str = default_field(metadata=meta(validate_duration))


@convertibleclass
class ProfileFields(Localizable):
    ADDITIONAL_CONTACT_DETAILS = "additionalContactDetails"
    DATE_OF_BIRTH = "dateOfBirth"
    BIOLOGICAL_SEX = "biologicalSex"
    ETHNICITY_OPTIONS = "ethnicityOptions"
    GENDER_OPTIONS = "genderOptions"
    VALIDATORS = "validators"
    MANDATORY_ONBOARDING_FIELDS = "mandatoryOnboardingFields"
    EXTRA_IDS = "extraIds"
    UN_EDITABLE_FIELDS = "unEditableFields"
    ORDERING = "ordering"
    EXCLUDED_FROM_ORDERING_FIELDS = "_excluded_from_ordering_fields"

    givenName: bool = field(default=True)
    familyName: bool = field(default=True)
    dateOfBirth: bool = default_field()  # default value (True) is set manually
    height: bool = field(default=False)
    gender: bool = field(default=True)
    biologicalSex: bool = default_field()  # default value (True) is set manually
    race: bool = field(default=False)
    ethnicity: bool = field(default=False)
    ethnicityOptions: list[EthnicityOption] = default_field()
    additionalContactDetails: AdditionalContactDetailsItem = default_field()
    mandatoryOnboardingFields: list[str] = default_field()
    extraIds: ProfileExtraIds = default_field()
    genderOptions: list[GenderOptionType] = default_field()
    bloodGroup: bool = field(default=False)

    phoneNumber: bool = field(default=True)
    email: bool = field(default=True)
    primaryAddress: bool = field(default=False)
    emergencyPhoneNumber: bool = field(default=False)

    familyMedicalHistory: bool = field(default=False)
    pastHistory: bool = field(default=False)
    presentSymptoms: bool = field(default=False)
    operationHistory: bool = field(default=False)
    chronicIllness: bool = field(default=False)
    allergyHistory: bool = field(default=False)
    pregnancy: bool = field(default=False)
    dateOfLastPhysicalExam: bool = field(default=False)

    unEditableFields: list[str] = default_field()
    validators: dict = dict_field(default=None, nested_cls=FieldValidator)
    ordering: list[str] = default_field()

    _localizableFields: tuple[str, ...] = (GENDER_OPTIONS, ETHNICITY_OPTIONS)
    _excluded_from_ordering_fields: tuple[str, ...] = (
        EXTRA_IDS,
        MANDATORY_ONBOARDING_FIELDS,
        UN_EDITABLE_FIELDS,
        VALIDATORS,
        Localizable.LOCALIZABLE_FIELDS,
        ORDERING,
        EXCLUDED_FROM_ORDERING_FIELDS,
    )

    @classmethod
    def get_orderable_fields(cls):
        return [
            field_name
            for field_name in cls.__dataclass_fields__
            if field_name not in cls._excluded_from_ordering_fields
        ]


@convertibleclass
class ClinicianOnlyFields:
    surgeryDateTime: bool = field(default=False)


@convertibleclass
class Profile(Localizable):
    FIELDS = "fields"
    CLINICIAN_ONLY_FIELDS = "clinicianOnlyFields"

    fields: ProfileFields = default_field()
    clinicianOnlyFields: ClinicianOnlyFields = default_field()

    _localizableFields: tuple[str, ...] = (FIELDS,)


class AppMenuItem(Enum):
    CARE_PLAN = "CARE_PLAN"
    KEY_ACTIONS = "KEY_ACTIONS"
    TO_DO = "TO_DO"
    TRACK = "TRACK"
    LEARN = "LEARN"
    PROFILE = "PROFILE"

    @staticmethod
    def default_app_view():
        return [
            AppMenuItem.CARE_PLAN,
            AppMenuItem.KEY_ACTIONS,
            AppMenuItem.LEARN,
            AppMenuItem.PROFILE,
        ]


@convertibleclass
class SurgeryDateRule:
    MAX_PAST_RANGE = "maxPastRange"
    MAX_FUTURE_RANGE = "maxFutureRange"

    DEFAULT_PAST_RANGE = "P1Y"
    DEFAULT_FUTURE_RANGE = "P2Y"

    maxPastRange: str = field(
        default=DEFAULT_PAST_RANGE, metadata=meta(validate_duration)
    )
    maxFutureRange: str = field(
        default=DEFAULT_FUTURE_RANGE, metadata=meta(validate_duration)
    )


class ReasonDetails:
    COMPLETED_TREATMENT: str = "hu_offboarding_reason_completed"
    DECEASED: str = "hu_offboarding_reason_deceased"
    LOST_TO_FOLLOW_UP: str = "hu_offboarding_reason_lost_to_follow_up"
    MONITORING_INAPPROPRIATE: str = "hu_offboarding_reason_inappropriate_monitoring"
    NO_LONGER_NEEDS_MONITORING: str = "hu_offboarding_reason_no_longer_monitoring"
    RECOVERED: str = "hu_offboarding_reason_recovered"


@convertibleclass
class Reason(Localizable):
    DISPLAY_NAME = "displayName"
    ORDER = "order"

    order: int = required_field(
        metadata=meta(validate_range(1, 100), value_to_field=int)
    )
    displayName: str = required_field(metadata=meta(validate_entity_name))

    _localizableFields: tuple[str, ...] = (DISPLAY_NAME,)

    @classmethod
    def _default_reasons_obj(cls):
        return [cls.from_dict(reason) for reason in cls._default_reasons()]

    @classmethod
    def _default_reasons(cls):
        return [
            {
                cls.DISPLAY_NAME: ReasonDetails.COMPLETED_TREATMENT,
                cls.ORDER: 1,
            },
            {
                cls.DISPLAY_NAME: ReasonDetails.DECEASED,
                cls.ORDER: 2,
            },
            {
                cls.DISPLAY_NAME: ReasonDetails.LOST_TO_FOLLOW_UP,
                cls.ORDER: 3,
            },
            {
                cls.DISPLAY_NAME: ReasonDetails.MONITORING_INAPPROPRIATE,
                cls.ORDER: 4,
            },
            {
                cls.DISPLAY_NAME: ReasonDetails.NO_LONGER_NEEDS_MONITORING,
                cls.ORDER: 5,
            },
            {
                cls.DISPLAY_NAME: ReasonDetails.RECOVERED,
                cls.ORDER: 6,
            },
        ]


@convertibleclass
class OffBoardingReasons:
    REASONS = "reasons"
    OTHER_REASON = "otherReason"

    reasons: list[Reason] = field(
        default_factory=Reason._default_reasons_obj,
        metadata=meta(
            validate_no_duplicate_keys_value_in_list(
                {Reason.DISPLAY_NAME, Reason.ORDER}
            )
        ),
    )
    otherReason: bool = field(default=True)


@convertibleclass
class Messaging(Localizable):
    ENABLED = "enabled"
    MESSAGES = "messages"

    class PredefinedMessages:
        MESSAGE1 = "Great job! Keep up the good work."

    _default_message = [PredefinedMessages.MESSAGE1]

    enabled: bool = field(default=False)
    messages: list[str] = default_field()
    allowCustomMessage: bool = field(default=False)

    _localizableFields: tuple[str, ...] = (MESSAGES,)

    def post_init(self):
        if not self.messages:
            self.messages = self._default_message


@convertibleclass
class SummaryReport:
    enabled: bool = field(default=False)


@convertibleclass
class BulkAction:
    enabled: bool = field(default=False)


@convertibleclass
class Features(Localizable):
    APP_MENU = "appMenu"
    APPOINTMENT = "appointment"
    CARE_PLAN_DAILY_ADHERENCE = "carePlanDailyAdherence"
    HEALTH_DEVICE_INTEGRATION = "healthDeviceIntegration"
    HIDE_APP_SUPPORT = "hideAppSupport"
    LABELS = "labels"
    MESSAGING = "messaging"
    OFF_BOARDING = "offBoarding"
    OFF_BOARDING_REASONS = "offBoardingReasons"
    PERSONAL_DOCUMENTS = "personalDocuments"
    PERSONALIZED_CONFIG = "personalizedConfig"
    PORTAL = "portal"
    PROXY = "proxy"
    SURGERY_DATE_RULE = "surgeryDateRule"
    BULK_ACTION = "bulkAction"
    LINK_INVITES = "linkInvites"

    appMenu: list[AppMenuItem] = field(
        default_factory=AppMenuItem.default_app_view,
        metadata=meta(validate_len(1, 4)),
    )
    appointment: bool = field(default=False)
    carePlanDailyAdherence: bool = field(default=False)
    healthDeviceIntegration: bool = field(default=False)
    offBoarding: bool = field(default=False)
    personalDocuments: bool = field(default=False)
    personalizedConfig: bool = field(default=False)
    proxy: bool = field(default=False)
    surgeryDateRule: SurgeryDateRule = default_field()
    labels: bool = field(default=False)
    portal: dict = default_field()
    offBoardingReasons: OffBoardingReasons = default_field()
    messaging: Messaging = default_field()
    hideAppSupport: bool = field(default=False)
    summaryReport: SummaryReport = default_field()
    bulkAction: BulkAction = default_field()
    linkInvites: bool = field(default=False)

    _localizableFields: tuple[str, ...] = (MESSAGING,)


@convertibleclass
class PAMIntegrationConfig:
    submitSurveyURI: str = required_field()
    enrollUserURI: str = required_field()
    clientExtID: str = required_field()
    clientPassKeyEncrypted: str = required_field()
    subgroupExtID: str = required_field()


@convertibleclass
class IntegrationConfig:
    pamConfig: PAMIntegrationConfig = default_field()


@convertibleclass
class FieldType(Enum):
    NUMERIC = "NUMERIC"
    TEXT = "TEXT"


@convertibleclass
class ExtraCustomFieldConfig(Localizable):
    ERROR_MESSAGE = "errorMessage"
    DESCRIPTION = "description"
    ONBOARDING_COLLECTION_TEXT = "onboardingCollectionText"
    ORDER = "order"
    PROFILE_COLLECTION_TEXT = "profileCollectionText"
    TYPE = "type"
    VALIDATION = "validation"

    clinicianUpdate: bool = field(default=True)
    errorMessage: str = required_field()
    description: str = default_field()
    onboardingCollectionText: str = required_field()
    order: int = required_field()
    profileCollectionText: str = required_field()
    required: bool = field(default=False)
    showClinicianHeader: bool = default_field()
    type: FieldType = required_field()
    validation: str = default_field(metadata=meta(validate_regex))
    isPrimary: bool = field(default=False)

    _localizableFields: tuple[str, ...] = (
        ERROR_MESSAGE,
        ONBOARDING_COLLECTION_TEXT,
        PROFILE_COLLECTION_TEXT,
        DESCRIPTION,
    )


@convertibleclass
class SurgeryDetailItem:
    KEY = "key"
    VALUE = "value"
    ORDER = "order"

    key: str = required_field(metadata=meta(not_empty))
    value: str = required_field(metadata=meta(not_empty))
    order: int = default_field(metadata=meta(lambda x: x >= 0))


@convertibleclass
class SurgeryDetail:
    DISPLAY_STRING = "displayString"
    PLACE_HOLDER = "placeHolder"
    ORDER = "order"
    ITEMS = "items"

    displayString: str = required_field(metadata=meta(not_empty))
    placeHolder: str = required_field(metadata=meta(not_empty))
    order: int = default_field(metadata=meta(lambda x: x >= 0))
    items: list[SurgeryDetailItem] = default_field(
        metadata=meta(not_empty, value_to_field=remove_duplicates)
    )

    def allowed_values(self):
        return [item.key for item in self.items]


@convertibleclass
class SurgeryDetails:
    OPERATION_TYPE = "operationType"
    IMPLANT_TYPE = "implantType"
    ROBOTIC_ASSISTANCE = "roboticAssistance"

    operationType: SurgeryDetail = default_field()
    implantType: SurgeryDetail = default_field()
    roboticAssistance: SurgeryDetail = default_field()

    def validate_input(self, surgery_details: dict) -> dict:
        """
        This method is used to validate user surgery details.
        Returns field_name: error if any:
        """
        error = {}
        for key, value in surgery_details.items():
            surgery_detail = getattr(self, key)
            if not surgery_detail:
                error[key] = f"Field {key} doesn't exist in surgery details config."
                continue

            if value not in surgery_detail.allowed_values():
                error[key] = f"Wrong value [{value}]"
        return error


@convertibleclass
class StaticEventConfig:
    title: str = required_field()
    description: str = required_field()


@convertibleclass
class Security:
    MFA_REQUIRED = "mfaRequired"
    APP_LOCK_REQUIRED = "appLockRequired"

    mfaRequired: bool = required_field()
    appLockRequired: bool = required_field()


@convertibleclass
class Location:
    ADDRESS = "address"
    COUNTRY = "country"
    COUNTRY_CODE = "countryCode"
    CITY = "city"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    POSTAL_CODE = "postalCode"
    STATE = "state"
    STREET = "street"

    address: str = default_field(metadata=meta(validator=validate_entity_name))
    country: str = default_field(metadata=meta(validate_country))
    countryCode: str = default_field(metadata=meta(validate_country_code))
    city: str = default_field(metadata=meta(validator=validate_entity_name))
    latitude: float = default_field()
    longitude: float = default_field()
    postalCode: str = default_field()
    state: str = default_field(metadata=meta(validator=validate_entity_name))
    street: str = default_field(metadata=meta(validator=validate_entity_name))


@convertibleclass
class Deployment(
    CarePlanGroupDeploymentExtension, CustomRolesExtension, LegalDocument, Localizable
):
    """Deployment model."""

    ID_ = "_id"
    ID = "id"
    DEPLOYMENT_ID = "deploymentId"
    NAME = "name"
    DESCRIPTION = "description"
    STATUS = "status"
    COLOR = "color"
    ICON = "icon"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    USER_ACTIVATION_CODE = "userActivationCode"
    MANAGER_ACTIVATION_CODE = "managerActivationCode"
    PROXY_ACTIVATION_CODE = "proxyActivationCode"
    MODULE_CONFIGS = "moduleConfigs"
    MODULE_CONFIG_ID = f"{MODULE_CONFIGS}.{ModuleConfig.ID}"
    LEARN = "learn"
    CONSENT = "consent"
    KEY_ACTIONS = "keyActions"
    CARE_PLAN_GROUP = "carePlanGroup"
    VERSION = "version"
    FIRST_VERSION = 0
    ECONSENT = "econsent"
    SURGERY_DETAILS = "surgeryDetails"
    CODE = "code"
    CONTACT_US_URL = "contactUsURL"
    ONFIDO_REQUIRED_REPORTS = "onfidoRequiredReports"
    ENROLLMENT_COUNTER = "enrollmentCounter"
    ONBOARDING_CONFIGS = "onboardingConfigs"
    STATS = "stats"
    LOCALIZATIONS = "localizations"
    PROFILE = "profile"
    FEATURES = "features"
    EXTRA_CUSTOM_FIELDS = "extraCustomFields"
    VALID_SORT_FIELDS = [NAME, ENROLLMENT_COUNTER, UPDATE_DATE_TIME]
    SECURITY = "security"
    LABELS = "labels"
    DASHBOARD_CONFIGURATION = "dashboardConfiguration"
    LOCATION = "location"
    COUNTRY = "country"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    name: str = default_field(metadata=meta(validate_entity_name))
    description: str = default_field(metadata=meta(validate_entity_name))
    status: Status = default_field()
    color: str = default_field(metadata=meta(validate_color))
    icon: S3Object = default_field()

    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    userActivationCode: str = default_field(metadata=meta(validate_activation_code))
    managerActivationCode: str = default_field(metadata=meta(validate_activation_code))
    proxyActivationCode: str = default_field(metadata=meta(validate_activation_code))
    moduleConfigs: list[ModuleConfig] = default_field()
    onboardingConfigs: list[OnboardingModuleConfig] = default_field()
    learn: Learn = default_field()
    consent: Consent = default_field()
    econsent: EConsent = default_field()
    keyActions: list[KeyActionConfig] = default_field()
    keyActionsEnabled: bool = default_field()
    profile: Profile = default_field()
    features: Features = default_field()
    extraCustomFields: dict = dict_field(
        default=None,
        nested_cls=ExtraCustomFieldConfig,
        metadata=meta(validate_len(0, 5)),
    )
    surgeryDetails: SurgeryDetails = default_field()
    contactUsURL: str = url_field()
    version: int = field(default=FIRST_VERSION)
    integration: IntegrationConfig = default_field()
    carePlanGroup: CarePlanGroup = default_field()
    language: str = field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )
    duration: str = default_field(metadata=meta(validate_duration))
    security: Security = default_field()
    mfaRequired: bool = default_field()  # deprecated
    code: str = default_field(metadata=meta(validate_entity_name))
    enrollmentCounter: int = default_field()
    staticEventConfig: StaticEventConfig = default_field()
    onfidoRequiredReports: list[OnfidoReportNameType] = default_field()
    stats: DeploymentStats = default_field()
    localizations: dict = default_field()
    country: str = default_field(metadata=meta(validate_country))
    dashboardConfiguration: DeploymentLevelConfiguration = default_field()
    labels: list[Label] = default_field(metadata=meta(validate_len(max=100)))
    location: Location = default_field()

    _localizableFields: tuple[str, ...] = (
        CONSENT,
        ECONSENT,
        MODULE_CONFIGS,
        LEARN,
        EXTRA_CUSTOM_FIELDS,
        KEY_ACTIONS,
        PROFILE,
        FEATURES,
    )

    @property
    def latest_consent(self):
        if self.consent and self.consent.enabled == EnableStatus.ENABLED:
            return self.consent

    @property
    def latest_econsent(self):
        if self.econsent and self.econsent.enabled == EnableStatus.ENABLED:
            return self.econsent

    def is_off_boarding_enabled(self):
        return self.features and self.features.offBoarding and self.duration

    def prepare_for_role(self, role: str, user_id: str):
        """Apply role requirements for deployment."""

        if role == RoleName.USER and self.features and self.features.personalizedConfig:
            custom_configs = fetch_custom_module_configs_of_user(user_id)
            self._merge_module_configs_with_custom_configs(custom_configs)

        self.prepare_module_configs_for_role(role)
        self._prepare_learn_articles_for_role(role)
        self._prepare_key_actions_for_role(role)
        self._prepare_onboarding_configs_for_role(role)

    def _merge_module_configs_with_custom_configs(
        self, custom_configs: list[CustomModuleConfig]
    ):
        if not custom_configs:
            return

        custom_configs_map = {conf.id: conf for conf in custom_configs}
        for index, config in enumerate(self.moduleConfigs):
            if config.id in custom_configs_map:
                original_config = config.to_dict(include_none=False)
                original_config.update(
                    custom_configs_map.get(config.id).to_dict(include_none=False)
                )
                self.moduleConfigs[index] = CustomModuleConfig.from_dict(
                    original_config
                )

    def _prepare_key_actions_for_role(self, role: str):
        if role == RoleName.PROXY:
            self.keyActions = []

    def _prepare_onboarding_configs_for_role(self, role_type: str):
        onboarding_configs = self.onboardingConfigs or []
        for onboarding_config in onboarding_configs:
            if not onboarding_config.is_valid_for(role_type):
                onboarding_config.status = EnableStatus.DISABLED

    def apply_care_plan_by_id(
        self, care_plan_group_id: str, user_id: str, role: str = RoleName.USER
    ):
        """
        Find care plan group by id and apply it's patches to current deployment.
        Filter module config and key actions based on new
        """
        if self.carePlanGroup and care_plan_group_id:
            care_plan_group = self.carePlanGroup.get_care_plan_group_by_id(
                care_plan_group_id, raise_error=True
            )
            self.moduleConfigs = self.patch_module_configs_by_group(care_plan_group)
        self.prepare_for_role(role, user_id)
        return self

    @property
    def observation_notes(self):
        configs = self.moduleConfigs or []
        filtered_configs = filter(
            lambda mc: mc.is_enabled() and mc.is_observation_note(), configs
        )
        return list(filtered_configs)

    def prepare_module_configs_for_role(self, role: str):
        module_configs = self.moduleConfigs or []
        enabled_ids = {mc.id for mc in module_configs if mc.is_valid_for(role)}
        self.moduleConfigs = [mc for mc in module_configs if mc.id in enabled_ids]

        self._filter_key_actions_for_enabled_modules(enabled_ids)

    def post_init(self):
        if self.mfaRequired is not None and not self.security:
            self.security = Security(
                mfaRequired=self.mfaRequired, appLockRequired=False
            )
        if not self.features:
            self.features = Features()
        if self.features and not self.features.offBoardingReasons:
            self.features.offBoardingReasons = OffBoardingReasons()
        else:
            if (
                not self.features.offBoardingReasons.reasons
                and not self.features.offBoardingReasons.otherReason
            ):
                raise ConvertibleClassValidationError(
                    f"It is forbidden to disable all options"
                )

    def filter_static_event_module_configs(self, user: User):
        if not self.moduleConfigs:
            return
        for config in list(self.moduleConfigs):
            # skipping if no life event panel config
            if not config.staticEvent:
                continue
            # calculating expiration
            expired = False
            duration = config.staticEvent.isoDuration

            if duration:
                duration = isodate.parse_duration(duration)
                expiration_date = user.createDateTime + duration
                expired = expiration_date <= datetime.utcnow()

            # keeping config if it's enabled and not expired
            if config.staticEvent.enabled and not expired:
                continue

            self.moduleConfigs.remove(config)

    def find_onboarding_config(self, module_id) -> Optional[OnboardingModuleConfig]:
        def find(mc: OnboardingModuleConfig) -> bool:
            return mc.onboardingId == module_id

        return next(filter(find, self.onboardingConfigs or []), None)

    def find_module_config(
        self, module_id: str, module_config_id: str = None
    ) -> Optional[ModuleConfig]:
        def find(mc: ModuleConfig) -> bool:
            condition = mc.moduleId == module_id
            if module_config_id:
                condition = condition and (mc.id == module_config_id)
            return condition

        return next(filter(find, self.moduleConfigs or []), None)

    def get_localization(
        self, locale: str = None, include_licensed: bool = True
    ) -> dict:
        """Gets localizations from deployments modules,
        for both normal and licensed questionnaire modules"""
        locale = locale or self.language
        default_localization = inject.instance(Localization).get(locale)
        deployment_localization = self.get_deployment_localization(locale)
        licensed_questionnaire_localization = (
            self.get_licensed_localization(locale) if include_licensed else {}
        )
        return {
            **default_localization,
            **deployment_localization,
            **licensed_questionnaire_localization,
        }

    def get_deployment_localization(self, locale):
        """Gets localizations from deployments modules,
        for normal (non-licensed) questionnaire modules"""
        deployment_localizations = self.localizations or {}
        if not (deployment_localization := deployment_localizations.get(locale)):
            deployment_localization = deployment_localizations.get(Language.EN, {})
        return deployment_localization

    def get_licensed_localization(self, locale):
        """Gets localizations from deployments modules,
        for licensed questionnaire modules"""
        from extensions.module_result.modules import licensed_questionnaire_module

        return licensed_questionnaire_module.get_localizations(
            locale, self.moduleConfigs
        )

    def generate_deployment_multi_language_state(self):
        deployment_copy = copy.deepcopy(self)
        return self._add_generated_localizations_to_deployment(deployment_copy)

    @staticmethod
    def _add_generated_localizations_to_deployment(deployment):
        # TODO: move 'hu' to configs
        if not deployment.localizations:
            localization_dict = (
                deployment.collect_localization_dict_and_replace_original_values(
                    path="hu"
                )
            )
            deployment.localizations = {Language.EN: localization_dict}
        else:
            localization_dict = (
                deployment.collect_localization_dict_and_replace_original_values(
                    path="hu",
                    translation_dict=deployment.localizations[Language.EN],
                )
            )
            deployment.localizations[Language.EN] = localization_dict

        return deployment

    def validate_keys_should_not_be_present_on_update(self):
        must_not_be_present(
            learn=self.learn,
            consent=self.consent,
            econsent=self.econsent,
            userActivationCode=self.userActivationCode,
            managerActivationCode=self.managerActivationCode,
            moduleConfigs=self.moduleConfigs,
            onboardingConfigs=self.onboardingConfigs,
            keyActions=self.keyActions,
            enrollmentCounter=self.enrollmentCounter,
            roles=self.roles,
            labels=self.labels,
        )

    @autoparams()
    def generate_presigned_urls_for_learn_article(
        self, file_storage: FileStorageAdapter
    ):
        if self.learn and self.learn.sections:
            for section in self.learn.sections:
                if not section.articles:
                    continue

                for article in section.articles:
                    if (
                        article.content
                        and article.content.contentObject
                        and not article.content.url
                    ):
                        content_object = article.content.contentObject
                        article.content.url = file_storage.get_pre_signed_url(
                            content_object.bucket, content_object.key
                        )

    def _filter_key_actions_for_enabled_modules(self, enabled_ids):
        key_actions = []
        for key_action in self.keyActions or []:
            if key_action.is_for_module():
                is_key_action_enabled = key_action.moduleConfigId in enabled_ids
                if is_key_action_enabled:
                    key_actions.append(key_action)
            else:
                key_actions.append(key_action)

        self.keyActions = key_actions

    def _prepare_learn_articles_for_role(self, role: str):
        if not (self.learn and self.learn.sections):
            return

        enabled_article_ids = []
        for section in self.learn.sections:
            section.prepare_for_role(role)
            for article in section.articles or []:
                enabled_article_ids.append(article.id)

        self._filter_key_actions_for_enabled_articles(enabled_article_ids)

    def _filter_key_actions_for_enabled_articles(self, enabled_ids: list[str]):
        key_actions = []
        for key_action in self.keyActions or []:
            if key_action.is_for_learn():
                is_key_action_enabled = key_action.learnArticleId in enabled_ids
                if is_key_action_enabled:
                    key_actions.append(key_action)
            else:
                key_actions.append(key_action)

        self.keyActions = key_actions

    def load_licensed_config_bodies(self):
        """Loads all config bodies regard to enabled module configs from licensed
        modules folders."""
        from extensions.module_result.modules.licensed_questionnaire_module import (
            get_licensed_questionnaires_dir_list,
            get_licensed_questionnaires_config_path,
            get_licensed_questionnaire_dir,
        )

        licensed_questionnaires_dir_list = get_licensed_questionnaires_dir_list()

        if not self.moduleConfigs:
            return

        for module_config in self.moduleConfigs:
            if (
                module_config.is_enabled()
                and module_config.moduleId in licensed_questionnaires_dir_list
            ):
                config_path = get_licensed_questionnaires_config_path(
                    module_config.moduleId
                )
                try:
                    module_config_from_file = read_json_file(
                        f"{get_licensed_questionnaire_dir()}/{config_path}", "./"
                    )
                except FileNotFoundError:
                    raise InvalidModuleConfiguration(
                        f"Config Body file not found for {module_config.moduleId}"
                    )
                else:
                    index = self.moduleConfigs.index(module_config)
                    module_config = module_config.to_dict(include_none=False)
                    merge_dicts(module_config, module_config_from_file)
                    self.moduleConfigs[index] = ModuleConfig.from_dict(
                        module_config, use_validator_field=False
                    )

    def populate_profile_fields_ordering(self):
        if not self.profile or not self.profile.fields:
            return
        predefined_order = self.profile.fields.ordering or []
        orderable_fields = ProfileFields.get_orderable_fields()
        missing_fields = [
            field_name
            for field_name in orderable_fields
            if field_name not in predefined_order
        ]
        self.profile.fields.ordering = [*predefined_order, *missing_fields]

    def preprocess_for_configuration(self):
        self.set_presigned_urls_for_legal_docs()
        self.generate_presigned_urls_for_learn_article()
        self.populate_profile_fields_ordering()
        self.load_licensed_config_bodies()


class ChangeType(Enum):
    MODULE_CONFIG = "MODULE_CONFIG"
    DEPLOYMENT = "DEPLOYMENT"
    ONBOARDING_CONFIG = "ONBOARDING_CONFIG"
    MULTI_LANGUAGE_CONVERSION = "MULTI_LANGUAGE_CONVERSION"


@convertibleclass
class DeploymentRevision:
    """Deployment Revision model."""

    ID = "id"
    ID_ = "_id"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    SUBMITTER_ID = "submitterId"
    CHANGE_TYPE = "changeType"
    DEPLOYMENT_ID = "deploymentId"
    VERSION = "version"
    SNAP = "snap"
    MODULE_CONFIG_ID = "moduleConfigId"
    ONBOARDING_CONFIG_ID = "onboardingConfigId"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    updateDateTime: datetime = field(
        default_factory=datetime.utcnow, metadata=default_datetime_meta()
    )
    createDateTime: datetime = field(
        default_factory=datetime.utcnow, metadata=default_datetime_meta()
    )
    submitterId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    changeType: ChangeType = default_field()
    deploymentId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    version: int = field(default=0)
    moduleConfigId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    onboardingConfigId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    snap: Deployment = default_field()


class TemplateCategory(Enum):
    CARDIOVASCULAR = "CARDIOVASCULAR"
    METABOLIC = "METABOLIC"
    RESPIRATORY = "RESPIRATORY"
    NEUROLOGY = "NEUROLOGY"
    MUSCULOSKELETAL = "MUSCULOSKELETAL"
    INFECTIOUS_DISEASES = "INFECTIOUS_DISEASES"
    SELF_SERVICE = "SELF_SERVICE"


@convertibleclass
class DeploymentTemplate:
    ID = "id"
    ID_ = "_id"
    NAME = "name"
    DESCRIPTION = "description"
    ORGANIZATION_IDS = "organizationIds"
    CATEGORY = "category"
    TEMPLATE = "template"
    STATUS = "status"
    IS_VERIFIED = "isVerified"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    name: str = required_field(metadata=meta(validate_len(1, 80)))
    description: str = required_field(metadata=meta(validate_len(1, 163)))
    organizationIds: list[str] = default_field(metadata=meta(validate_object_ids))
    category: TemplateCategory = required_field()
    template: Deployment = default_field()
    status: EnableStatus = field(default=EnableStatus.ENABLED)
    isVerified: bool = field(default=False)
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


class DeploymentAction(Enum):
    CreateDeployment = "CreateDeployment"
    UpdateDeployment = "UpdateDeployment"
    DeleteDeployment = "DeleteDeployment"

    CreateConsent = "CreateConsent"
    CreateEConsent = "CreateEConsent"
    CreateCarePlanGroup = "CreateCarePlanGroup"
    CreateOrUpdateRoles = "CreateOrUpdateRoles"
    CreateLocalization = "CreateLocalization"

    CreateLearnSection = "CreateLearnSection"
    UpdateLearnSection = "UpdateLearnSection"
    DeleteLearnSection = "DeleteLearnSection"

    CreateArticle = "CreateArticle"
    UpdateArticle = "UpdateArticle"
    DeleteArticle = "DeleteArticle"

    CreateModuleConfig = "CreateModuleConfig"
    UpdateModuleConfig = "UpdateModuleConfig"
    DeleteModuleConfig = "DeleteModuleConfig"

    CreateOnboardingModuleConfig = "CreateOnboardingModuleConfig"
    UpdateOnboardingModuleConfig = "UpdateOnboardingModuleConfig"
    DeleteOnboardingModuleConfig = "DeleteOnboardingModuleConfig"

    CreateKeyActionConfig = "CreateKeyActionConfig"
    UpdateKeyActionConfig = "UpdateKeyActionConfig"
    DeleteKeyActionConfig = "DeleteKeyActionConfig"

    CreateLabel = "CreateLabel"
    UpdateLabel = "UpdateLabel"
    DeleteLabel = "DeleteLabel"

    GenerateMasterTranslation = "GenerateMasterTranslation"

    CreateDeploymentTemplate = "CreateDeploymentTemplate"
    UpdateDeploymentTemplate = "UpdateDeploymentTemplate"
    DeleteDeploymentTemplate = "DeleteDeploymentTemplate"
