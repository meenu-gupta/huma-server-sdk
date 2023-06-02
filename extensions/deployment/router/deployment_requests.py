import logging
import re
from dataclasses import fields
from datetime import datetime

from extensions.authorization.boarding.manager import BoardingManager
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.sort import SortField
from extensions.common.validators import (
    validate_custom_unit,
    validate_ethnicity_options,
    validate_fields_for_cls,
    validate_gender_options,
)
from extensions.deployment.models.care_plan_group.care_plan_group import CarePlanGroup
from extensions.deployment.models.care_plan_group.group import Group
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import (
    Deployment,
    DeploymentTemplate,
    ModuleConfig,
    OnboardingModuleConfig,
    Profile,
    ProfileFields,
    Security,
    TemplateCategory,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.models.key_action_config import (
    KeyActionConfig,
    validate_duration_iso,
)
from extensions.deployment.models.learn import (
    LearnArticle,
    LearnSection,
    OrderUpdateObject,
)
from extensions.deployment.models.status import Status
from extensions.deployment.use_case.file_library_metadata import STANDARD_LIBRARIES
from sdk.common.exceptions.exceptions import InvalidRequestException, PermissionDenied
from sdk.common.localization.utils import validate_localizations
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    ConvertibleClassValidationError,
    convertibleclass,
    default_field,
    meta,
    positive_integer_field,
    required_field,
)
from sdk.common.utils.validators import (
    check_if_only_one_default,
    check_unique_values,
    default_datetime_meta,
    must_be_only_one_of,
    must_be_present,
    must_not_be_present,
    not_empty,
    not_empty_list,
    validate_len,
    validate_object_id,
)

log = logging.getLogger(__name__)


def validate_profile_fields(deployment: Deployment, cls=User):
    profile_field_exist = deployment.profile and deployment.profile.fields

    if profile_field_exist and deployment.profile.fields.genderOptions:
        validate_gender_options(deployment.profile.fields.genderOptions)

    if profile_field_exist and deployment.profile.fields.ethnicityOptions:
        validate_ethnicity_options(deployment.profile.fields.ethnicityOptions)

    if profile_field_exist and deployment.profile.fields.validators:
        validate_fields_for_cls(deployment.profile.fields.validators, cls)


def extra_validate_duration_iso(iso_duration: str) -> bool:
    if not re.search(r"[1-9]", iso_duration):
        raise Exception("Not allowed to have 0 interval")

    return validate_duration_iso(iso_duration=iso_duration)


@convertibleclass
class CreateDeploymentRequestObject(Deployment):
    @classmethod
    def validate(cls, deployment):
        must_not_be_present(
            id=deployment.id,
            learn=deployment.learn,
            consent=deployment.consent,
            userActivationCode=deployment.userActivationCode,
            managerActivationCode=deployment.managerActivationCode,
            moduleConfigs=deployment.moduleConfigs,
            onboardingConfigs=deployment.onboardingConfigs,
            keyActions=deployment.keyActions,
            roles=deployment.roles,
            enrollmentCounter=deployment.enrollmentCounter,
            updateDateTime=deployment.updateDateTime,
            createDateTime=deployment.createDateTime,
        )
        must_be_present(name=deployment.name)

        if deployment.status == Status.ARCHIVED:
            raise InvalidRequestException("status can NOT be ARCHIVED")

        validate_profile_fields(deployment=deployment)

    def post_init(self):
        super().post_init()
        self._set_default_value_for_profile_fields_if_not_set()

    def _set_default_value_for_profile_fields_if_not_set(self):
        if not self.profile:
            self.profile = Profile()
        if not self.profile.fields:
            profile_fields = {_field.name: None for _field in fields(ProfileFields)}
            profile_fields.update(
                {
                    "biologicalSex": True,
                    "dateOfBirth": True,
                    "mandatoryOnboardingFields": [
                        ProfileFields.BIOLOGICAL_SEX,
                        ProfileFields.DATE_OF_BIRTH,
                    ],
                }
            )
            self.profile.fields = ProfileFields(**profile_fields)
        elif self.profile.fields:
            self._init_profile_fields(ProfileFields.DATE_OF_BIRTH)
            self._init_profile_fields(ProfileFields.BIOLOGICAL_SEX)

    def _init_profile_fields(self, profile_field: str):

        mob_fields_list = self.profile.fields.mandatoryOnboardingFields
        mob_fields_set = set(mob_fields_list) if mob_fields_list else set()

        profile_field_value = getattr(self.profile.fields, profile_field)

        if profile_field_value is None:
            setattr(self.profile.fields, profile_field, True)
            mob_fields_set.add(profile_field)

        elif not profile_field_value and profile_field in mob_fields_set:
            mob_fields_set.remove(profile_field)

        self.profile.fields.mandatoryOnboardingFields = list(mob_fields_set)


@convertibleclass
class CreateConsentRequestObject(Consent):
    @classmethod
    def validate(cls, consent):
        must_not_be_present(id=consent.id, createDateTime=consent.createDateTime)
        must_be_present(enabled=consent.enabled)


@convertibleclass
class CreateLearnSectionRequestObject(LearnSection):
    @classmethod
    def validate(cls, learn_section):
        must_not_be_present(
            id=learn_section.id,
            updateDateTime=learn_section.updateDateTime,
            createDateTime=learn_section.createDateTime,
            articles=learn_section.articles,
        )


@convertibleclass
class CreateLearnArticleRequestObject(LearnArticle):
    @classmethod
    def validate(cls, article):
        must_not_be_present(
            id=article.id,
            updateDateTime=article.updateDateTime,
            createDateTime=article.createDateTime,
        )


@convertibleclass
class CreateModuleConfigRequestObject(ModuleConfig):
    @classmethod
    def validate(cls, module_config):
        must_not_be_present(
            id=module_config.id,
            updateDateTime=module_config.updateDateTime,
            createDateTime=module_config.createDateTime,
        )

        must_be_present(
            moduleConfigId=module_config.moduleId,
            moduleConfigStatus=module_config.status,
        )
        ModuleConfig.validate(module_config)
        if module_config.customUnit:
            validate_custom_unit(module_config.customUnit)


class OnboardingRequestObject(OnboardingModuleConfig):
    @classmethod
    def validate(cls, onboarding_module_config):
        must_be_present(
            onboardingId=onboarding_module_config.onboardingId,
            order=onboarding_module_config.order,
        )
        _validate_onboarding_config_body(
            onboarding_module_config.onboardingId, onboarding_module_config.configBody
        )


@convertibleclass
class CreateOnboardingConfigRequestObject(OnboardingRequestObject):
    pass


@convertibleclass
class UpdateOnboardingConfigRequestObject(OnboardingRequestObject):
    pass


@convertibleclass
class DeleteOnboardingConfigRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    ONBOARDING_ID = "onboardingId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    onboardingId: str = required_field(metadata=meta(validate_object_id))


def _validate_onboarding_config_body(onboarding_id: str, config_body: dict):
    BoardingManager.validate_onboarding_config_body(onboarding_id, config_body)


@convertibleclass
class CreateKeyActionConfigRequestObject(KeyActionConfig):

    durationIso: str = required_field(metadata=meta(extra_validate_duration_iso))
    notifyEvery: str = default_field(metadata=meta(extra_validate_duration_iso))

    @classmethod
    def validate(cls, action: KeyActionConfig):
        must_not_be_present(
            id=action.id,
            updateDateTime=action.updateDateTime,
            createDateTime=action.createDateTime,
        )

        must_be_only_one_of(
            learnArticleId=action.learnArticleId, moduleId=action.moduleId
        )

        if action.type == cls.Type.MODULE:
            must_be_present(
                moduleId=action.moduleId, moduleConfigId=action.moduleConfigId
            )
        elif action.type == cls.Type.LEARN:
            must_be_present(learnArticleId=action.learnArticleId)


@convertibleclass
class UpdateModuleConfigRequestObject(ModuleConfig):
    @classmethod
    def validate(cls, module_config: ModuleConfig):
        must_not_be_present(
            updateDateTime=module_config.updateDateTime,
            createDateTime=module_config.createDateTime,
        )

        must_be_present(moduleId=module_config.moduleId, status=module_config.status)
        ModuleConfig.validate(module_config)


@convertibleclass
class UpdateLearnSectionRequestObject(LearnSection):
    @classmethod
    def validate(cls, section_obj):
        must_not_be_present(
            articles=section_obj.articles,
            updateDateTime=section_obj.updateDateTime,
            createDateTime=section_obj.createDateTime,
        )

        must_be_present(learnSectionId=section_obj.id)


@convertibleclass
class UpdateArticleRequestObject(LearnArticle):
    @classmethod
    def validate(cls, article_obj):
        must_not_be_present(
            updateDateTime=article_obj.updateDateTime,
            createDateTime=article_obj.createDateTime,
        )

        must_be_present(articleId=article_obj.id)


@convertibleclass
class UpdateKeyActionConfigRequestObject(CreateKeyActionConfigRequestObject):
    @classmethod
    def validate(cls, action: KeyActionConfig):
        must_be_present(id=action.id)


@convertibleclass
class SignConsentRequestObject(ConsentLog):
    @classmethod
    def validate(cls, consent_log):
        must_not_be_present(
            id=consent_log.id,
            createDateTime=consent_log.createDateTime,
            revision=consent_log.revision,
        )

        must_be_present(userId=consent_log.userId, consentId=consent_log.consentId)


@convertibleclass
class RetrieveDeploymentsRequestObject:
    SKIP = "skip"
    LIMIT = "limit"
    SEARCH_CRITERIA = "searchCriteria"
    SORT = "sort"
    NAME_CONTAINS = "nameContains"
    STATUS = "status"

    skip: int = positive_integer_field(default=None)
    limit: int = positive_integer_field(default=None)
    searchCriteria: str = default_field()
    sort: list[SortField] = default_field()
    status: list[Status] = default_field()

    # @deprecated, use `searchCriteria` instead
    nameContains: str = default_field()

    def __iter__(self):
        return iter(self.__dict__.values())


@convertibleclass
class RetrieveDeploymentRequestObject:
    DEPLOYMENT_ID = "deploymentId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveDeploymentByRevisionRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    VERSION_NUMBER = "versionNumber"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    versionNumber: int = default_field()


@convertibleclass
class RetrieveLatestConsentRequestObject:
    DEPLOYMENT_ID = "deploymentId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveLabelsRequestObject:
    DEPLOYMENT_ID = "deploymentId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class CreateLabelsRequestObject(RetrieveLabelsRequestObject):
    TEXTS = "texts"
    SUBMITTER_ID = "submitterId"

    submitterId: str = required_field(metadata=meta(validate_object_id))
    texts: list[str] = required_field(metadata=meta(not_empty_list))


@convertibleclass
class UpdateLabelRequestObject(RetrieveLabelsRequestObject):
    TEXT = "text"
    LABEL_ID = "labelId"
    SUBMITTER_ID = "submitterId"

    submitterId: str = required_field(metadata=meta(validate_object_id))
    text: str = required_field(metadata=meta(lambda n: not_empty))
    labelId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteLabelRequestObject(RetrieveLabelsRequestObject):

    LABEL_ID = "labelId"

    labelId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UpdateDeploymentRequestObject(Deployment):
    version: int = default_field()

    @classmethod
    def validate(cls, deployment: Deployment):
        deployment.validate_keys_should_not_be_present_on_update()
        must_not_be_present(
            createDateTime=deployment.createDateTime,
            updateDateTime=deployment.updateDateTime,
            version=deployment.version,
        )
        must_be_present(id=deployment.id)

        primary_fields_count = 0
        for name, config in (deployment.extraCustomFields or {}).items():
            if config.isPrimary:
                primary_fields_count += 1
        if primary_fields_count > 1:
            raise ConvertibleClassValidationError(
                "Only one Primary Field can exist per deployment."
            )

        validate_profile_fields(deployment=deployment)

    def post_init(self):
        if self.mfaRequired is not None and not self.security:
            self.security = Security(
                mfaRequired=self.mfaRequired, appLockRequired=False
            )


@convertibleclass
class DeleteDeploymentRequestObject:
    DEPLOYMENT_ID = "deploymentId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteModuleConfigRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    MODULE_CONFIG_ID = "moduleConfigId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    moduleConfigId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteLearnSectionRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    SECTION_ID = "sectionId"
    USER_ID = "userId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    sectionId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteArticleRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    SECTION_ID = "sectionId"
    ARTICLE_ID = "articleId"
    USER_ID = "userId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    sectionId: str = required_field(metadata=meta(validate_object_id))
    articleId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteKeyActionRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    KEY_ACTION_CONFIG_ID = "keyActionConfigId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    keyActionConfigId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class EncryptValueRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    VALUE = "value"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    value: str = required_field(metadata=meta(lambda n: not_empty))


@convertibleclass
class CreateCarePlansRequestObject(CarePlanGroup):
    @classmethod
    def validate(cls, care_plan_group):
        must_be_present(groups=care_plan_group.groups)
        check_if_only_one_default(arr=care_plan_group.groups, key=Group.DEFAULT)
        check_unique_values(
            arr=care_plan_group.groups,
            keys=[Group.ID, Group.EXTENSION_FOR_ACTIVATION_CODE],
        )


def _validate_econsent_sections(sections: list[EConsentSection]):
    for section in sections:
        if section.contentType == EConsentSection.ContentType.IMAGE:
            must_not_be_present(
                videoUrl=section.videoUrl, videoLocation=section.videoLocation
            )
            must_be_only_one_of(
                thumbnailUrl=section.thumbnailUrl,
                thumbnailLocation=section.thumbnailLocation,
            )
        elif section.contentType == EConsentSection.ContentType.VIDEO:
            must_be_only_one_of(
                thumbnailUrl=section.thumbnailUrl,
                thumbnailLocation=section.thumbnailLocation,
            )
            must_be_only_one_of(
                videoUrl=section.videoUrl, videoLocation=section.videoLocation
            )


@convertibleclass
class CreateEConsentRequestObject(EConsent):
    @classmethod
    def validate(cls, econsent):
        must_not_be_present(id=econsent.id, createDateTime=econsent.createDateTime)

        must_be_present(
            enabled=econsent.enabled,
            title=econsent.title,
            overviewText=econsent.overviewText,
            contactText=econsent.contactText,
        )

        _validate_econsent_sections(econsent.sections)


@convertibleclass
class SignEConsentRequestObject(EConsentLog):
    USER = "user"
    REQUEST_ID = "requestId"

    requestId: str = required_field(metadata=meta(validate_len(32, 36)))
    user: AuthorizedUser = required_field()

    @classmethod
    def validate(cls, econsent_log):
        must_not_be_present(
            id=econsent_log.id,
            createDateTime=econsent_log.createDateTime,
            revision=econsent_log.revision,
            pdfLocation=econsent_log.pdfLocation,
        )
        if econsent_log.consentOption == EConsentLog.EConsentOption.NOT_PARTICIPATE:
            must_be_present(
                userId=econsent_log.userId, econsentId=econsent_log.econsentId
            )
        else:
            must_be_present(
                userId=econsent_log.userId,
                econsentId=econsent_log.econsentId,
                signature=econsent_log.signature,
            )


@convertibleclass
class WithdrawEConsentRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    ECONSENT_ID = "econsentId"
    LOG_ID = "logId"
    USER_ID = "userId"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    econsentId: str = required_field(metadata=meta(validate_object_id))
    logId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeploymentRoleUpdateObject:
    DEPLOYMENT_ID = "deploymentId"
    ROLES = "roles"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    roles: list[Role] = default_field()

    @classmethod
    def validate(cls, instance):
        default_roles = inject.instance(DefaultRoles)
        roles = instance.roles or []
        role_names = set(role.name for role in roles)
        if len(role_names) != len(instance.roles):
            raise InvalidRequestException("Can't create multiple roles with same name.")

        msg_template = "Custom role name cannot be one of default roles %s"
        for role in roles:
            must_be_present(
                name=role.name, permissions=role.has_extra_permissions() or None
            )
            is_default_role = role.name.lower() in {x.lower() for x in default_roles}
            if is_default_role:
                msg = msg_template % f"[{', '.join(default_roles)}]"
                raise InvalidRequestException(msg)


@convertibleclass
class AddUserNotesRequestObject:
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    DEPLOYMENT_ID = "deploymentId"
    NOTE = "note"
    CREATE_DATE_TIME = "createDateTime"

    userId: str = required_field(metadata=meta(validate_object_id))
    submitterId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    deploymentId: str = required_field(metadata=meta(validate_object_id))
    note: str = required_field(metadata=meta(not_empty))
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class RetrieveUserNotesRequestObject:
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    SKIP = "skip"
    LIMIT = "limit"

    userId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))
    skip: int = positive_integer_field(default=None)
    limit: int = positive_integer_field(default=None)


@convertibleclass
class UpdateLocalizationsRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    LOCALIZATIONS = "localizations"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    localizations: dict = required_field(metadata=meta(validate_localizations))


@convertibleclass
class CloneDeploymentRequestObject:
    NAME = "name"
    REFERENCE_ID = "referenceId"

    name: str = required_field()
    referenceId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class ReorderRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    ITEMS = "items"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    items: list[OrderUpdateObject] = required_field()


@convertibleclass
class ReorderLearnArticles(ReorderRequestObject):
    SECTION_ID = "sectionId"

    sectionId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveLocalizableFieldsRequestObject(RetrieveDeploymentRequestObject):
    pass


@convertibleclass
class GenerateMasterTranslationRequestObject(RetrieveDeploymentRequestObject):
    pass


@convertibleclass
class RetrieveDeploymentKeyActionsRequestObject:
    START_DATE = "startDate"
    END_DATE = "endDate"
    TRIGGER_TIME = "triggerTime"
    DEPLOYMENT_ID = "deploymentId"

    startDate: datetime = required_field(metadata=default_datetime_meta())
    endDate: datetime = required_field(metadata=default_datetime_meta())
    triggerTime: datetime = default_field(metadata=default_datetime_meta())
    deploymentId: str = required_field(metadata=meta(validate_object_id))

    def post_init(self):
        if not self.triggerTime:
            self.triggerTime = datetime.utcnow()


@convertibleclass
class CreateMultipleModuleConfigsRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    MODULE_CONFIGS = "moduleConfigs"

    deploymentId: str = required_field(metadata=meta(validate_object_id))
    moduleConfigs: list[CreateModuleConfigRequestObject] = required_field(
        metadata=meta(not_empty)
    )


@convertibleclass
class CreateDeploymentTemplateRequestObject(DeploymentTemplate):
    SUBMITTER = "submitter"

    submitter: AuthorizedUser = default_field()

    @classmethod
    def validate(cls, deployment_template):
        must_not_be_present(id=deployment_template.id)
        if deployment_template.category == TemplateCategory.SELF_SERVICE:
            must_be_present(organizationIds=deployment_template.organizationIds)

        cls._validate_permission_based_on_user_role(deployment_template)
        cls._remove_unneeded_fields_from_template(deployment_template.template)
        deployment_template.__delattr__(cls.SUBMITTER)

    @staticmethod
    def _validate_permission_based_on_user_role(
        deployment_template: DeploymentTemplate,
    ):
        role_assignment = deployment_template.submitter.role_assignment.roleId

        if role_assignment in {RoleName.SUPER_ADMIN, RoleName.HUMA_SUPPORT}:
            if deployment_template.category == TemplateCategory.SELF_SERVICE:
                raise PermissionDenied
            return

        elif role_assignment == RoleName.ACCOUNT_MANAGER:
            if deployment_template.category != TemplateCategory.SELF_SERVICE:
                raise PermissionDenied

            if deployment_template.isVerified is True:
                raise PermissionDenied

            user_orgs = deployment_template.submitter.organization_ids()
            for org in deployment_template.organizationIds:
                if org not in user_orgs:
                    raise PermissionDenied
            return

    @staticmethod
    def _remove_unneeded_fields_from_template(deployment_template: Deployment):
        template_fields_to_exist = {
            Deployment.DESCRIPTION,
            Deployment.STATUS,
            Deployment.MODULE_CONFIGS,
            Deployment.LEARN,
            Deployment.CONSENT,
            Deployment.KEY_ACTIONS,
            Deployment.CARE_PLAN_GROUP,
            Deployment.ECONSENT,
            Deployment.SURGERY_DETAILS,
            Deployment.PRIVACY_POLICY_URL,
            Deployment.EULA_URL,
            Deployment.CONTACT_US_URL,
            Deployment.TERM_AND_CONDITION_URL,
            Deployment.ONFIDO_REQUIRED_REPORTS,
            Deployment.ONBOARDING_CONFIGS,
            Deployment.LOCALIZATIONS,
            Deployment.PROFILE,
            Deployment.FEATURES,
            Deployment.EXTRA_CUSTOM_FIELDS,
            Deployment.PRIVACY_POLICY_OBJECT,
            Deployment.TERM_AND_CONDITION_OBJECT,
            Deployment.EULA_OBJECT,
        }
        for field_name in deployment_template.__annotations__.keys():
            if field_name not in template_fields_to_exist:
                deployment_template.__delattr__(field_name)


@convertibleclass
class RetrieveDeploymentTemplatesRequestObject:
    ORGANIZATION_ID = "organizationId"
    SUBMITTER = "submitter"

    submitter: AuthorizedUser = default_field()
    organizationId: str = default_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, instance):
        if instance.submitter.role_assignment.roleId in {
            RoleName.ACCOUNT_MANAGER,
            RoleName.ORGANIZATION_EDITOR,
            RoleName.ORGANIZATION_OWNER,
        }:
            must_be_present(id=instance.organizationId)
            user_orgs = instance.submitter.organization_ids()
            if instance.organizationId not in user_orgs:
                raise PermissionDenied
            return


@convertibleclass
class RetrieveDeploymentTemplateRequestObject(RetrieveDeploymentTemplatesRequestObject):
    TEMPLATE_ID = "templateId"

    templateId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteDeploymentTemplateRequestObject(RetrieveDeploymentTemplateRequestObject):
    @classmethod
    def validate(cls, instance):
        if instance.submitter.role_assignment == RoleName.ACCOUNT_MANAGER:
            user_orgs = instance.submitter.organization_ids()
            if instance.organizationId not in user_orgs:
                raise PermissionDenied


@convertibleclass
class UpdateDeploymentTemplateRequestObject:
    TEMPLATE_ID = "templateId"
    ORGANIZATION_ID = "organizationId"
    UPDATE_DATA = "updateData"
    SUBMITTER = "submitter"

    submitter: AuthorizedUser = default_field()
    templateId: str = required_field(metadata=meta(validate_object_id))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    updateData: DeploymentTemplate = required_field()

    @classmethod
    def validate(cls, instance):
        role_id = instance.submitter.role_assignment.roleId
        if role_id in {RoleName.SUPER_ADMIN, RoleName.HUMA_SUPPORT}:
            if instance.updateData.category == TemplateCategory.SELF_SERVICE:
                raise PermissionDenied
            return

        if role_id == RoleName.ACCOUNT_MANAGER:
            must_be_present(id=instance.organizationId)
            user_orgs = instance.submitter.organization_ids()
            if instance.organizationId not in user_orgs:
                raise PermissionDenied

            if instance.updateData.category != TemplateCategory.SELF_SERVICE:
                raise PermissionDenied

            if instance.updateData.isVerified is True:
                raise PermissionDenied


@convertibleclass
class FileLibraryRequestObject:
    USER_ID = "userId"
    LIBRARY_ID = "libraryId"
    DEPLOYMENT_ID = "deploymentId"

    userId: str = default_field(metadata=meta(validate_object_id))
    libraryId: str = required_field(metadata=meta(not_empty))
    deploymentId: str = default_field(metadata=meta(validate_object_id))

    @inject.autoparams("repo")
    def check_permission(self, repo: AuthorizationRepository):
        user = repo.retrieve_simple_user_profile(user_id=self.userId)
        authz_user = AuthorizedUser(user)
        if not authz_user.is_super_admin():
            raise PermissionDenied
        if self.deploymentId and self.deploymentId not in authz_user.deployment_ids():
            raise PermissionDenied

    @classmethod
    def validate(cls, request):
        is_deployment_library = request.libraryId not in STANDARD_LIBRARIES
        if is_deployment_library and not request.deploymentId:
            msg = (
                f"Deployment ID is required for accessing files in {request.libraryId}"
            )
            raise InvalidRequestException(msg)


@convertibleclass
class AddFilesToLibraryRequestObject(FileLibraryRequestObject):
    FILE_IDS = "fileIds"

    fileIds: list[str] = required_field(metadata=meta(not_empty_list))


@convertibleclass
class RetrieveFilesInLibraryRequestObject(FileLibraryRequestObject):
    OFFSET = "offset"
    LIMIT = "limit"

    offset: int = positive_integer_field(default=0)
    limit: int = positive_integer_field(default=100)


@convertibleclass
class LibraryFileObject:
    ID = "id"
    FILE_NAME = "fileName"
    FILE_SIZE = "fileSize"
    CONTENT_TYPE = "contentType"
    METADATA = "metadata"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    fileName: str = default_field()
    fileSize: int = default_field()
    contentType: str = default_field()
    metadata: dict = default_field()


@convertibleclass
class RetrieveFilesInLibraryResponseObject:
    FILES = "files"

    files: list[LibraryFileObject] = default_field()
