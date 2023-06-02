from dataclasses import field
from datetime import datetime, date
from enum import Enum, IntEnum
from typing import Optional

from extensions.authorization import validators
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.common.exceptions import UserAttributeMissingError
from extensions.common.s3object import S3Object
from extensions.deployment.exceptions import DeploymentErrorCodes
from sdk.common.common_models.user_models import AddressObject
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    ConvertibleClassValidationError,
    convertibleclass,
    default_field,
    meta,
    required_field,
)
from sdk.common.utils.date_utils import calculate_age
from sdk.common.utils.validators import (
    validate_timezone,
    validate_object_id,
    utc_str_to_date,
    default_datetime_meta,
    validate_entity_name,
    validate_len,
    not_empty,
    default_email_meta,
    incorrect_language_to_default,
    validate_range,
    utc_str_val_to_field,
    default_phone_number_meta,
    validate_phone_number,
    str_id_to_obj_id,
    utc_str_field_to_val,
    utc_date_to_str,
    validate_resource,
)


@convertibleclass
class TaskCompliance:
    CURRENT = "current"
    TOTAL = "total"
    DUE = "due"
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    START_DATE_TIME = "startDateTime"
    PERCENTAGE = "percentage"
    CURRENT_PERIOD = "currentPeriod"
    TOTAL_PERIOD = "totalPeriod"
    TOTAL_COMPLIANCE = "totalCompliance"
    PERIOD_PROGRESS = "periodProgress"

    COMPLETED_KEY_ACTIONS = "completedKeyActions"
    ALL_KEY_ACTIONS = "allKeyActions"

    current: int = default_field()
    total: int = default_field()
    due: int = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    percentage: int = default_field()

    def post_init(self):
        if self.total and self.current is not None:
            self.percentage = round(self.current * 100 / self.total)


@convertibleclass
class UserStats:
    TASK_COMPLIANCE = "taskCompliance"
    STUDY_PROGRESS = "studyProgress"
    taskCompliance: TaskCompliance = default_field()


@convertibleclass
class PersonalDocument:
    class PersonalDocumentMediaType(Enum):
        PHOTO = "PHOTO"
        PDF = "PDF"

    NAME = "name"
    FILE_TYPE = "fileType"
    FILE_OBJECT = "fileObject"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    name: str = required_field(metadata=meta(validator=validate_entity_name))
    fileType: PersonalDocumentMediaType = required_field()
    fileObject: S3Object = required_field()
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class RoleAssignment:
    DEPLOYMENT = "deployment"
    ORGANIZATION = "organization"
    USER = "user"

    ROLE_ID = "roleId"
    RESOURCE = "resource"
    USER_TYPE = "userType"

    roleId: str = required_field(default=RoleName.USER)
    resource: str = required_field(metadata=meta(validator=validate_resource))
    userType: str = default_field()

    def __str__(self):
        return f"{self.roleId} on resource[{self.resource}]"

    def __eq__(self, other):
        if not isinstance(other, RoleAssignment):
            return False
        return self.roleId == other.roleId and self.resource == other.resource

    def post_init(self):
        self._set_user_type()

    @classmethod
    def create_super_admin(cls):
        return cls._create_role(RoleName.SUPER_ADMIN, f"{cls.DEPLOYMENT}/*")

    @classmethod
    def create_huma_support(cls):
        return cls._create_role(RoleName.HUMA_SUPPORT, f"{cls.DEPLOYMENT}/*")

    @classmethod
    def create_proxy(cls, user_id: str):
        return cls._create_role(RoleName.PROXY, f"{cls.USER}/{user_id}")

    @classmethod
    def create_role(cls, role_id: str, resource_id: str, resource_name: str = None):
        super_roles = [RoleName.SUPER_ADMIN, RoleName.HUMA_SUPPORT]
        if role_id not in super_roles and not resource_id:
            msg = f"Cannot create {role_id} with no resource"
            raise ConvertibleClassValidationError(msg)

        if role_id == RoleName.SUPER_ADMIN:
            return cls.create_super_admin()

        if role_id == RoleName.HUMA_SUPPORT:
            return cls.create_huma_support()

        if not resource_name:
            if validators.check_role_id_valid_for_organization(role_id, resource_id):
                resource_name = cls.ORGANIZATION
            elif validators.check_role_id_valid_for_resource(
                role_id, resource_id, "deployment"
            ):
                resource_name = cls.DEPLOYMENT
            else:
                raise ConvertibleClassValidationError(
                    f"Role [{role_id}] is not a valid RoleName"
                )

        resource = f"{resource_name}/{resource_id}"

        return cls._create_role(role_id, resource)

    @classmethod
    def _create_role(cls, role: str, resource: str):
        role_dict = {
            RoleAssignment.ROLE_ID: role,
            RoleAssignment.RESOURCE: resource,
        }
        return cls.from_dict(role_dict)

    def resource_name(self):
        (resource_name, _) = self.resource.split("/")
        return resource_name

    def resource_id(self):
        (_, resource_id) = self.resource.split("/")
        return resource_id

    def is_deployment(self):
        return self.DEPLOYMENT == self.resource_name()

    def is_multi_resource(self):
        return self.roleId in RoleName.multi_deployment_roles()

    def is_org(self):
        return self.ORGANIZATION == self.resource_name()

    def is_proxy(self):
        return "user" in (self.resource or "") and self.roleId == RoleName.PROXY

    def is_wildcard(self):
        return self.resource_id() == "*"

    def _set_user_type(self):
        if self.userType:
            return

        role = inject.instance(DefaultRoles).get(self.roleId)
        if not role:
            if self.resource_name() == self.DEPLOYMENT:
                from extensions.authorization.helpers import get_deployment_custom_role

                role = get_deployment_custom_role(self.roleId, self.resource_id())
            elif self.resource_name() == self.ORGANIZATION:
                from extensions.authorization.helpers import (
                    get_organization_custom_role,
                )

                role = get_organization_custom_role(self.roleId, self.resource_id())

        self.userType = role.userType if role else None


@convertibleclass
class UserSurgeryDetails:
    OPERATION_TYPE = "operationType"
    IMPLANT_TYPE = "implantType"
    ROBOTIC_ASSISTANCE = "roboticAssistance"

    operationType: str = default_field(metadata=meta(not_empty))
    implantType: str = default_field(metadata=meta(not_empty))
    roboticAssistance: str = default_field(metadata=meta(not_empty))


@convertibleclass
class UserLabel:

    LABEL_ID = "labelId"
    ASSIGNED_BY = "assignedBy"
    ASSIGN_DATE_TIME = "assignDateTime"

    labelId: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    assignedBy: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    assignDateTime: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class BoardingStatus:
    class Status(IntEnum):
        ACTIVE = 0
        OFF_BOARDED = 1

    class ReasonOffBoarded(IntEnum):
        USER_NO_CONSENT = 0
        USER_FAIL_ID_VERIFICATION = 1
        USER_FAIL_PRE_SCREENING = 2
        USER_COMPLETE_ALL_TASK = 3
        USER_MANUAL_OFF_BOARDED = 4
        USER_FAIL_HELPER_AGREEMENT = 5
        USER_UNSIGNED_EICF = 6
        USER_WITHDRAW_EICF = 7

    OFF_BOARDED_EXCEPTION = {
        ReasonOffBoarded.USER_NO_CONSENT: DeploymentErrorCodes.OFF_BOARDING_USER_NO_CONSENT,
        ReasonOffBoarded.USER_FAIL_ID_VERIFICATION: DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_ID_VERIFICATION,
        ReasonOffBoarded.USER_FAIL_PRE_SCREENING: DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_PRE_SCREENING,
        ReasonOffBoarded.USER_COMPLETE_ALL_TASK: DeploymentErrorCodes.OFF_BOARDING_USER_COMPLETE_ALL_TASK,
        ReasonOffBoarded.USER_MANUAL_OFF_BOARDED: DeploymentErrorCodes.OFF_BOARDING_USER_MANUAL_OFF_BOARDED,
        ReasonOffBoarded.USER_FAIL_HELPER_AGREEMENT: DeploymentErrorCodes.OFF_BOARDING_USER_FAIL_HELPER_AGREEMENT,
        ReasonOffBoarded.USER_UNSIGNED_EICF: DeploymentErrorCodes.OFF_BOARDING_USER_UNSIGNED_EICF,
        ReasonOffBoarded.USER_WITHDRAW_EICF: DeploymentErrorCodes.OFF_BOARDING_USER_WITHDRAW_EICF,
    }

    STATUS = "status"
    UPDATE_DATE_TIME = "updateDateTime"
    SUBMITTER_ID = "submitterId"
    REASON_OFF_BOARDED = "reasonOffBoarded"
    DETAILS_OFF_BOARDED = "detailsOffBoarded"

    status: Status = required_field(default=Status.ACTIVE.value)
    updateDateTime: datetime = field(
        default_factory=datetime.utcnow,
        metadata=meta(
            field_to_value=utc_str_field_to_val,
            value_to_field=utc_str_val_to_field,
        ),
    )
    submitterId: str = default_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    reasonOffBoarded: ReasonOffBoarded = default_field()
    detailsOffBoarded: str = default_field()

    def is_off_boarded(self):
        return self.status == self.Status.OFF_BOARDED

    def get_reason_off_board_error_code(self) -> int:
        reason = self.reasonOffBoarded and self.reasonOffBoarded.value
        return self.OFF_BOARDED_EXCEPTION.get(reason, DeploymentErrorCodes.OFF_BOARDING)


@convertibleclass
class AdditionalContactDetails:
    ALT_CONTACT_NUMBER = "altContactNumber"
    REGULAR_CONTACT_NAME = "regularContactName"
    REGULAR_CONTACT_NUMBER = "regularContactNumber"
    EMERGENCY_CONTACT_NAME = "emergencyContactName"
    EMERGENCY_CONTACT_NUMBER = "emergencyContactNumber"

    altContactNumber: str = default_field(metadata=meta(not_empty))
    regularContactName: str = default_field(metadata=meta(validate_entity_name))
    regularContactNumber: str = default_field(metadata=meta(validate_phone_number))
    emergencyContactName: str = default_field(metadata=meta(validate_entity_name))
    emergencyContactNumber: str = default_field(metadata=meta(validate_phone_number))


@convertibleclass
class Flags:
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    GRAY = "gray"

    red: int = default_field()
    amber: int = default_field()
    green: int = default_field()
    gray: int = default_field()


@convertibleclass
class UnseenFlags(Flags):
    pass


@convertibleclass
class RecentFlags(Flags):
    pass


@convertibleclass
class User:
    class VerificationStatus(IntEnum):
        ID_VERIFICATION_SUCCEEDED = 1
        ID_VERIFICATION_FAILED = 2
        ID_VERIFICATION_IN_PROCESS = 3
        ID_VERIFICATION_NEEDED = 4

    class Gender(Enum):
        MALE = "MALE"
        FEMALE = "FEMALE"
        NOT_KNOWN = "NOT_KNOWN"
        NOT_SPECIFIED = "NOT_SPECIFIED"  # i.e. prefer not to say
        NON_BINARY = "NON_BINARY"
        TRANSGENDER = "TRANSGENDER"
        OTHER = "OTHER"
        AGENDER_OR_TRANSGENDER = "AGENDER_OR_TRANSGENDER"

        @classmethod
        def has_value(cls, value):
            return value in cls.__members__

    class BiologicalSex(Enum):
        MALE = "MALE"
        FEMALE = "FEMALE"
        OTHER = "OTHER"
        NOT_SPECIFIED = "NOT_SPECIFIED"

    class Ethnicity(Enum):
        WHITE = "WHITE"
        MIXED_OR_MULTI_ETHNIC_GROUPS = "MIXED_OR_MULTI_ETHNIC_GROUPS"
        ASIAN_OR_ASIAN_BRITISH = "ASIAN_OR_ASIAN_BRITISH"
        BLACK_OR_AFRICAN_OR_CARIBBEAN_OR_BLACK_BRITISH = (
            "BLACK_OR_AFRICAN_OR_CARIBBEAN_OR_BLACK_BRITISH"
        )
        OTHER_ETHNIC_GROUPS = "OTHER_ETHNIC_GROUPS"
        ASIAN_AMERICAN = "ASIAN_AMERICAN"
        BLACK_AFRICAN = "BLACK_AFRICAN"
        HISPANIC = "HISPANIC"

        @classmethod
        def has_value(cls, value):
            return value in cls.__members__

    ID_ = "_id"
    ID = "id"
    STATUS = "status"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    SURGERY_DATE_TIME = "surgeryDateTime"
    LAST_SUBMIT_DATE_TIME = "lastSubmitDateTime"
    SURGERY_DETAILS = "surgeryDetails"
    DATE_OF_BIRTH = "dateOfBirth"
    GIVEN_NAME = "givenName"
    GENDER = "gender"
    BIOLOGICAL_SEX = "biologicalSex"
    FAMILY_NAME = "familyName"
    EMAIL = "email"
    PHONE_NUMBER = "phoneNumber"
    ACTIVATION_CODE = "activationCode"
    MASTER_KEY = "masterKey"
    ROLES = "roles"
    TIMEZONE = "timezone"
    RECENT_MODULE_RESULTS = "recentModuleResults"
    TAGS = "tags"
    TAGS_AUTHOR_ID = "tagsAuthorId"
    EXTRA_CUSTOM_FIELDS = "extraCustomFields"
    HEIGHT = "height"
    ADDITIONAL_CONTACT_DETAILS = "additionalContactDetails"
    CARE_PLAN_GROUP_ID = "carePlanGroupId"
    PREFERRED_UNITS = "preferredUnits"
    NHS = "nhsId"
    ADDRESS_OBJECT = "addressComponent"
    ONFIDO_APPLICANT_ID = "onfidoApplicantId"
    VERIFICATION_STATUS = "verificationStatus"
    PERSONAL_DOCUMENTS = "personalDocuments"
    FINISHED_ONBOARDING = "finishedOnboarding"
    ENROLLMENT_ID = "enrollmentId"
    ENROLLMENT_NUMBER = "enrollmentNumber"
    BOARDING_STATUS = "boardingStatus"
    LANGUAGE = "language"
    WECHAT_ID = "wechatId"
    KARDIA_ID = "kardiaId"
    INSURANCE_NUMBER = "insuranceNumber"
    PAM_THIRD_PARTY_IDENTIFIER = "pamThirdPartyIdentifier"
    EMERGENCY_PHONE_NUMBER = "emergencyPhoneNumber"
    PRIMARY_ADDRESS = "primaryAddress"
    STATS = "stats"
    FAMILY_MEDICAL_HISTORY = "familyMedicalHistory"
    DEPLOYMENTS = "deployments"
    RAG_SCORE = "ragScore"
    FLAGS = "flags"
    UNSEEN_FLAGS = "unseenFlags"
    RECENT_FLAGS = "recentFlags"
    BADGES = "badges"
    LAST_LOGIN_DATE_TIME = "lastLoginDateTime"
    LABELS = "labels"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    lastSubmitDateTime: datetime = default_field(metadata=default_datetime_meta())
    givenName: str = default_field(metadata=meta(validate_entity_name))
    familyName: str = default_field(metadata=meta(validate_entity_name))
    gender: Gender = default_field()
    biologicalSex: BiologicalSex = default_field()
    ethnicity: Ethnicity = default_field()
    dateOfBirth: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date),
    )
    email: str = default_field(metadata=default_email_meta())
    phoneNumber: str = default_field(metadata=default_phone_number_meta())
    primaryAddress: str = default_field(metadata=meta(validate_len(0, 256)))
    race: str = default_field(metadata=meta(validate_len(1, 49)))
    bloodGroup: str = default_field(metadata=meta(validate_len(1, 19)))
    emergencyPhoneNumber: str = default_field(metadata=default_phone_number_meta())
    # height unit is centimeter and the value between 90 cm to 250 cm
    height: float = default_field(
        metadata=meta(validator=lambda h: 90 <= h <= 250, value_to_field=float)
    )
    additionalContactDetails: AdditionalContactDetails = default_field()
    familyMedicalHistory: str = default_field()
    pastHistory: str = default_field()
    presentSymptoms: str = default_field()
    operationHistory: str = default_field()
    chronicIllness: str = default_field()
    allergyHistory: str = default_field()
    pregnancy: str = default_field()
    dateOfLastPhysicalExam: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date),
    )
    extraCustomFields: dict = default_field()
    surgeryDetails: UserSurgeryDetails = default_field()
    # extra IDs
    fenlandCohortId: str = default_field()
    nhsId: str = default_field()
    insuranceNumber: str = default_field()
    wechatId: str = default_field()
    kardiaId: str = default_field()
    pamThirdPartyIdentifier: str = default_field()

    roles: list[RoleAssignment] = default_field()
    timezone: str = default_field(metadata=meta(validate_timezone))
    recentModuleResults: dict = default_field()
    tags: dict = default_field()
    labels: list[UserLabel] = default_field(metadata=meta(validate_len(max=20)))
    tagsAuthorId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )
    surgeryDateTime: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date),
    )
    carePlanGroupId: str = default_field()
    preferredUnits: dict = default_field()
    addressComponent: AddressObject = default_field()
    onfidoApplicantId: str = default_field()
    verificationStatus: VerificationStatus = default_field()
    personalDocuments: list[PersonalDocument] = default_field()
    enrollmentId: int = default_field(metadata=meta(validate_range(1)))
    enrollmentNumber: str = default_field()
    deployments: list[str] = default_field()
    boardingStatus: BoardingStatus = default_field()
    language: str = default_field(
        metadata=meta(value_to_field=incorrect_language_to_default)
    )
    # got to home screen at least once
    finishedOnboarding: bool = default_field()
    stats: UserStats = default_field()
    ragScore: list[int] = default_field()
    flags: UnseenFlags = default_field()
    unseenFlags: UnseenFlags = default_field()
    recentFlags: RecentFlags = default_field()
    lastLoginDateTime: datetime = default_field(metadata=default_datetime_meta())
    badges: dict = default_field()

    def __str__(self):
        boarding_status = None
        if self.boardingStatus:
            boarding_status = f"{self.boardingStatus.status.name}"
            if self.boardingStatus.status == BoardingStatus.Status.OFF_BOARDED:
                boarding_status += (
                    f", {User.BOARDING_STATUS}.{BoardingStatus.REASON_OFF_BOARDED}: "
                    f"{self.boardingStatus.reasonOffBoarded.name}"
                )

        rtrn = (
            f"[{User.__name__} {User.ID}: {self.id}, "
            f"{User.ROLES}: {[] if not self.roles else [role.roleId for role in self.roles]}, "
            f"{User.TIMEZONE}: {self.timezone}, "
            f"{User.LAST_LOGIN_DATE_TIME}: {self.lastLoginDateTime}, "
            f"{User.FINISHED_ONBOARDING}: {self.finishedOnboarding}, "
            f"{User.BOARDING_STATUS}: {boarding_status}]"
        )
        return rtrn

    def read_only_fields(self):
        """
        These fields are added to model dynamically on retrieval and can't be stored in DB
        """
        return {
            self.DEPLOYMENTS,
            self.ENROLLMENT_NUMBER,
            self.RAG_SCORE,
            self.FLAGS,
            self.BADGES,
        }

    @staticmethod
    def public_fields() -> dict:
        return {
            user_field: True
            for user_field in User.__dict__.keys()
            if not user_field[0].isupper() and "_" not in user_field
        }

    @staticmethod
    def private_fields() -> list:
        return [
            user_field
            for user_field in User.__dict__.keys()
            if user_field[0].isupper() or "_" in user_field
        ]

    @staticmethod
    def identifiers_fields():
        return {
            User.NHS,
            User.DATE_OF_BIRTH,
            User.EMAIL,
            User.GIVEN_NAME,
            User.FAMILY_NAME,
            User.ID,
        }

    @staticmethod
    def identifiable_data_fields():
        return {
            User.GIVEN_NAME,
            User.FAMILY_NAME,
            User.NHS,
            User.EMAIL,
            User.DATE_OF_BIRTH,
            User.PHONE_NUMBER,
        }

    def get_age(self) -> int:
        if self.dateOfBirth:
            return calculate_age(self.dateOfBirth)
        raise UserAttributeMissingError(self.DATE_OF_BIRTH)

    def get_full_name(self) -> str:
        return f"{self.givenName or ''} {self.familyName or ''}".strip()

    def remove_roles(self, roles_ids, resource_id) -> bool:
        def is_deleted_role(role):
            return role.roleId in roles_ids and resource_id in role.resource

        roles_count = len(self.roles)
        self.roles = [role for role in self.roles if not is_deleted_role(role)]
        return bool(roles_count - len(self.roles))

    def has_boarding_status(self):
        try:
            return bool(self.boardingStatus.status)
        except AttributeError:
            return False

    def is_off_boarded(self):
        return bool(self.boardingStatus and self.boardingStatus.status)

    def get_preferred_units_for_module(self, module_id: str) -> Optional[str]:
        return self.preferredUnits and self.preferredUnits.get(module_id)
