from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from extensions.authorization.models.manager_assigment import ManagerAssignment
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import (
    User,
    RoleAssignment,
    PersonalDocument,
    BoardingStatus,
    UserStats,
    TaskCompliance,
)
from extensions.authorization.validators import (
    check_role_id_valid_for_resource,
    is_common_role,
    validate_common_role_edit_levels,
    is_common_role_editable_role,
    validate_same_resource_level,
)
from extensions.common.s3object import S3Object
from extensions.common.validators import validate_tag, validate_fields_for_cls
from extensions.deployment.models.care_plan_group.care_plan_group import (
    CarePlanGroupLog,
)
from extensions.deployment.models.deployment import Deployment
from sdk.common.exceptions.exceptions import InvalidRoleException, PermissionDenied
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    ConvertibleClassValidationError,
    required_field,
    positive_integer_field,
    natural_number_field,
    default_field,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import (
    must_not_be_present,
    validate_entity_name,
    validate_email,
    not_empty,
    validate_non_empty_object_ids,
    validate_object_id,
    must_be_present,
    must_not_be_empty_list,
    validate_language,
    validate_object_ids,
)

DEFAULT_PROFILE_RESULT_PAGE_SIZE = 20


@convertibleclass
class RetrieveUserProfileRequestObject:
    USER_ID = "userId"
    CAN_VIEW_IDENTIFIER_DATA = "canViewIdentifierData"
    IS_MANAGER = "isManager"
    DEPLOYMENT_ID = "deploymentId"
    CALLER_LANGUAGE = "callerLanguage"

    userId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    canViewIdentifierData: bool = field(default=False)
    isManager: bool = field(default=False)
    callerLanguage: str = default_field()


@convertibleclass
class SortParameters:
    STATUS = "status"
    FIELDS = "fields"
    ORDER = "order"

    class Status(Enum):
        CONTINUE_MONITORING = "continueMonitoring"
        DECEASED = "deceased"
        FLAGGED = "flagged"
        INPATIENT = "inpatient"
        NEEDS_ADMISSION = "needsAdmission"
        RECOVERED = "recovered"

    class Field(Enum):
        LAST_UPDATED = User.LAST_SUBMIT_DATE_TIME
        DOB = User.DATE_OF_BIRTH
        SURGERY_DATE = User.SURGERY_DATE_TIME
        RAG = "rag"
        FLAGS = "flags"
        MODULE = "module"
        GIVEN_NAME = User.GIVEN_NAME
        FAMILY_NAME = User.FAMILY_NAME
        BOARDING_STATUS = "onboardingStatus"
        BOARDING_SURGERY_DATE_TIME = f"{User.BOARDING_STATUS}.surgeryDateTime"
        BOARDING_UPDATE_DATE_TIME = (
            f"{User.BOARDING_STATUS}.{BoardingStatus.UPDATE_DATE_TIME}"
        )
        BOARDING_DETAILS_OFF_BOARDED = (
            f"{User.BOARDING_STATUS}.{BoardingStatus.DETAILS_OFF_BOARDED}"
        )
        BOARDING_REASON_OFF_BOARDED = (
            f"{User.BOARDING_STATUS}.{BoardingStatus.REASON_OFF_BOARDED}"
        )
        TASK_COMPLIANCE = (
            f"{User.STATS}.{UserStats.TASK_COMPLIANCE}.{TaskCompliance.PERCENTAGE}"
        )
        DEPLOYMENT_ID = f"{User.ROLES}.0.{RoleAssignment.RESOURCE}"
        ID = "_id"

    class Order(Enum):
        DESCENDING = -1
        ASCENDING = 1

    @convertibleclass
    class Extra:
        moduleId: str = required_field(metadata=meta(not_empty))
        moduleConfigId: str = required_field(metadata=meta(validate_object_id))

    status: list[Status] = default_field()
    fields: list[Field] = default_field()
    extra: Extra = default_field()
    order: Order = default_field()

    @classmethod
    def validate(cls, sort: "SortParameters"):
        if sort.fields and cls.Field.MODULE in sort.fields:
            must_be_present(extra=sort.extra)
            if len(sort.fields) != 1:
                raise ConvertibleClassValidationError(
                    f"Sorting by {cls.Field.MODULE} doesn't support multiple fields sorting"
                )
        else:
            must_not_be_present(extra=sort.extra)


@convertibleclass
class RetrieveProfilesRequestObject:
    DEPLOYMENT_ID = "deploymentId"
    CLEAN = "clean"
    ROLE = "role"
    CAN_VIEW_IDENTIFIER_DATA = "canViewIdentifierData"
    SORT = "sort"
    SEARCH = "search"
    SKIP = "skip"
    LIMIT = "limit"
    MANAGER_ID = "managerId"
    HASH = "hash"
    ENABLED_MODULE_IDS = "enabledModuleIds"
    FILTERS = "filters"
    SUBMITTER = "submitter"

    search: str = default_field()
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    role: str = field(default=Role.UserType.USER)
    patientIdentifiersOnly: bool = field(default=False)
    patientDataOnly: bool = field(default=False)
    # if clean=True, all additional data won't be added(seen, thresholds, etc)
    clean: bool = field(default=False)
    canViewIdentifierData: bool = field(default=False)
    skip: int = positive_integer_field(default=0)
    limit: int = natural_number_field(default=DEFAULT_PROFILE_RESULT_PAGE_SIZE)
    sort: SortParameters = default_field()
    managerId: str = default_field(metadata=meta(validate_object_id))
    filters: dict = default_field(
        metadata=meta(lambda f: validate_fields_for_cls(f, User))
    )
    hash: str = default_field()
    enabledModuleIds: list[str] = default_field()
    submitter: AuthorizedUser = required_field()

    @classmethod
    def validate(cls, request_object):
        super_roles = [Role.UserType.SUPER_ADMIN, RoleName.HUMA_SUPPORT]
        if request_object.role in super_roles:
            raise ConvertibleClassValidationError(
                f"Role [{request_object.role}] is not valid RoleName"
            )
        if not request_object.managerId:
            must_be_present(deploymentId=request_object.deploymentId)

        if filters := request_object.filters:
            if (labels := filters.get(User.LABELS)) and not validate_object_ids(labels):
                raise ConvertibleClassValidationError(
                    message=f"Invalid label id in {labels}"
                )

    def has_sort_fields(self):
        try:
            return bool(self.sort.fields and self.sort.order)
        except AttributeError:
            return False

    def is_for_users(self):
        return self.role and self.role == Role.UserType.USER

    def is_complex_sort_request(self):
        if not self.has_sort_fields():
            return False

        if SortParameters.Field.RAG in self.sort.fields:
            return True

        return False


@convertibleclass
class UpdateUserRoleRequestObject:
    NOT_ALLOWED_ROLES = (
        RoleName.SUPER_ADMIN,
        RoleName.HUMA_SUPPORT,
        RoleName.USER,
    )

    ROLES = "roles"
    SUBMITTER = "submitter"

    roles: list[RoleAssignment] = required_field()
    submitter: AuthorizedUser = required_field()

    @classmethod
    @autoparams()
    def validate(cls, instance, default_roles: DefaultRoles):
        roles: list[RoleAssignment] = instance.roles
        deployment_roles = default_roles.deployment
        org_roles = default_roles.organization
        invalid_roles = set()
        submitter_role = instance.submitter.get_role().id
        for role in roles:
            if role.roleId in cls.NOT_ALLOWED_ROLES:
                invalid_roles.add(role.roleId)
                continue

            if submitter_role in deployment_roles and role.roleId in org_roles:
                raise PermissionDenied

            if submitter_role in org_roles and role.roleId in deployment_roles:
                raise PermissionDenied

            cls.validate_role(role, instance.submitter)

        if invalid_roles:
            error_msg = "Roles [%s] can't be assigned to."
            raise InvalidRoleException(error_msg % ",".join(invalid_roles))

    @classmethod
    def validate_role(cls, role: RoleAssignment, submitter: AuthorizedUser):
        if role.is_deployment():
            allowed_resources = submitter.deployment_ids()
        elif role.is_org():
            allowed_resources = submitter.organization_ids()
        else:
            raise PermissionDenied

        if role.resource_id() not in allowed_resources:
            raise PermissionDenied


@convertibleclass
class UpdateRolesRequestObject:
    NOT_ALLOWED_ROLES = (
        RoleName.SUPER_ADMIN,
        RoleName.HUMA_SUPPORT,
        RoleName.USER,
    )

    USER_ID = "userId"
    ROLES = "roles"
    SUBMITTER = "submitter"

    userId: str = required_field()
    submitter: AuthorizedUser = required_field()
    roles: list[RoleAssignment] = required_field(metadata=meta(not_empty))

    @staticmethod
    def check_permission(roles: list[dict], submitter: AuthorizedUser):
        for role in roles:
            if not isinstance(role, RoleAssignment):
                role = RoleAssignment.from_dict(role)

            UpdateRolesRequestObject._check_permission(role, submitter)

    @staticmethod
    def _check_permission(role, submitter: AuthorizedUser):
        if submitter.is_super_admin():
            return

        allowed_resources = []
        if is_common_role(role.roleId):
            if role.resource_name() == "organization":
                allowed_resources = submitter.organization_ids()
            elif role.resource_name() == "deployment":
                allowed_resources = submitter.deployment_ids()
        elif role.is_deployment():
            allowed_resources = submitter.deployment_ids()
        elif role.is_org():
            allowed_resources = submitter.organization_ids()
        else:
            raise PermissionDenied

        if role.resource_id() not in allowed_resources:
            raise PermissionDenied


class AddRolesRequestObject(UpdateRolesRequestObject):
    @classmethod
    def validate(cls, instance):
        if len(instance.roles) > 1:
            if not all(role.is_multi_resource() for role in instance.roles):
                msg = f"All roles should support multiple resources"
                raise InvalidRoleException(msg)

        for role in instance.roles:
            if role.roleId in cls.NOT_ALLOWED_ROLES:
                raise InvalidRoleException(f"Role {role} can't be assigned to.")

            if is_common_role(instance.submitter.role_assignment.roleId):
                validate_common_role_edit_levels(
                    instance.submitter.role_assignment.resource_name(),
                    role.resource_name(),
                )
                if not is_common_role_editable_role(role.roleId):
                    raise InvalidRoleException
            else:
                validate_same_resource_level(instance.submitter.role_assignment, role)

            if not check_role_id_valid_for_resource(role.roleId, role.resource_id()):
                raise ConvertibleClassValidationError(
                    f"Role [{role.roleId}] is not valid"
                )


@convertibleclass
class AddRolesToUsersRequestObject:
    NOT_ALLOWED_ROLES = (
        RoleName.SUPER_ADMIN,
        RoleName.HUMA_SUPPORT,
        RoleName.USER,
    )

    USER_IDS = "userIds"
    ALL_USERS = "allUsers"
    ROLES = "roles"
    SUBMITTER = "submitter"

    userIds: list[str] = default_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    allUsers: bool = field(default=False)
    submitter: AuthorizedUser = required_field()
    roles: list[RoleAssignment] = required_field(metadata=meta(not_empty))

    @classmethod
    def validate(cls, request_object):
        if not request_object.allUsers:
            must_not_be_empty_list(userIds=request_object.userIds)

        if len(request_object.roles) > 1:
            if not all(role.is_multi_resource() for role in request_object.roles):
                msg = f"All roles should support multiple resources"
                raise InvalidRoleException(msg)

        if is_common_role(request_object.submitter.role_assignment.roleId):
            cls.NOT_ALLOWED_ROLES += tuple(
                set(RoleName.org_roles() + RoleName.deployment_roles())
                - set(RoleName.common_roles())
            )
        else:
            cls.NOT_ALLOWED_ROLES += RoleName.common_roles()

        for role in request_object.roles:
            if role.roleId in cls.NOT_ALLOWED_ROLES:
                raise InvalidRoleException(f"Role {role} can't be assigned to.")

            if is_common_role(request_object.submitter.role_assignment.roleId):
                validate_common_role_edit_levels(
                    request_object.submitter.role_assignment.resource_name(),
                    role.resource_name(),
                )
                if not is_common_role_editable_role(role.roleId):
                    raise InvalidRoleException
            else:
                validate_same_resource_level(
                    request_object.submitter.role_assignment, role
                )
            if not check_role_id_valid_for_resource(role.roleId, role.resource_id()):
                raise ConvertibleClassValidationError(
                    f"Role [{role.roleId}] is not valid"
                )

    @staticmethod
    def check_permission(roles: list[dict], submitter: AuthorizedUser):
        UpdateRolesRequestObject.check_permission(roles, submitter)


class RemoveRolesRequestObject(UpdateRolesRequestObject):
    @classmethod
    def validate(cls, instance):
        for role in instance.roles:
            if role.roleId in cls.NOT_ALLOWED_ROLES:
                raise InvalidRoleException(f"Role {role} can't be assigned to.")

            if is_common_role(instance.submitter.role_assignment.roleId):
                validate_common_role_edit_levels(
                    instance.submitter.role_assignment.resource_name(),
                    role.resource_name(),
                )
                if not is_common_role_editable_role(role.roleId):
                    raise InvalidRoleException
            else:
                validate_same_resource_level(instance.submitter.role_assignment, role)


@convertibleclass
class UpdateUserProfileRequestObject(User):
    PREVIOUS_STATE = "previousState"

    deviceName: str = default_field(metadata=meta(validate_entity_name))
    previousState: User = default_field()

    @classmethod
    def validate(cls, user):
        must_not_be_present(
            email=user.email,
            phoneNumber=user.phoneNumber,
            roles=user.roles,
            recentModuleResults=user.recentModuleResults,
            tags=user.tags,
            enrollmentId=user.enrollmentId,
            boardingStatus=user.boardingStatus,
            personalDocuments=user.personalDocuments,
            lastSubmitDateTime=user.lastSubmitDateTime,
            **{key: getattr(user, key) for key in user.read_only_fields()},
        )


@convertibleclass
class FinishUserOnBoardingRequestObject(User):
    PREVIOUS_STATE = "previousState"

    previousState: User = default_field()

    @classmethod
    def validate(cls, user):
        must_not_be_present(
            email=user.email,
            phoneNumber=user.phoneNumber,
            roles=user.roles,
            recentModuleResults=user.recentModuleResults,
            tags=user.tags,
            enrollmentId=user.enrollmentId,
            personalDocuments=user.personalDocuments,
            lastSubmitDateTime=user.lastSubmitDateTime,
            **{key: getattr(user, key) for key in user.read_only_fields()},
        )


@convertibleclass
class CreateTagRequestObject:
    TAGS = "tags"
    TAGS_AUTHOR_ID = "tagsAuthorId"
    USER_ID = "userId"

    tags: dict = required_field(metadata=meta(validate_tag))
    tagsAuthorId: str = required_field()
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class BaseUserLabelRequestObject:
    LABEL_IDS = "labelIds"
    ASSIGNED_BY = "assignedBy"
    DEPLOYMENT_ID = "deploymentId"

    assignedBy: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class AssignLabelsToUsersRequestObject(BaseUserLabelRequestObject):
    USER_IDS = "userIds"

    labelIds: list[str] = required_field(metadata=meta(validate_non_empty_object_ids))
    userIds: list[str] = required_field(metadata=meta(validate_non_empty_object_ids))


@convertibleclass
class AssignLabelsToUserRequestObject(BaseUserLabelRequestObject):
    USER_ID = "userId"

    labelIds: list[str] = required_field(metadata=meta(validate_object_ids))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteTagRequestObject:
    TAGS_AUTHOR_ID = "tagsAuthorId"
    USER_ID = "userId"

    tagsAuthorId: str = required_field()
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class AssignManagerRequestObject(ManagerAssignment):
    @classmethod
    def validate(cls, request_object):
        must_not_be_present(
            createDateTime=request_object.createDateTime,
            updateDateTime=request_object.updateDateTime,
        )


@convertibleclass
class AssignManagersToUsersRequestObject:
    MANAGER_IDS = "managerIds"
    USER_IDS = "userIds"
    ALL_USERS = "allUsers"
    SUBMITTER_ID = "submitterId"

    managerIds: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    userIds: list[str] = default_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    allUsers: bool = field(default=False)
    submitterId: str = required_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, request_object):
        if not request_object.allUsers:
            must_not_be_empty_list(userIds=request_object.userIds)


@convertibleclass
class RetrieveAssignedProfilesRequestObject:
    MANAGER_ID = "managerId"
    managerId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UpdateUserCarePlanGroupRequestObject(CarePlanGroupLog):
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"
    DEPLOYMENT_ID = "deploymentId"
    CARE_PLAN_GROUP_ID = "carePlanGroupId"
    NOTE = "note"

    carePlanGroupId: str = required_field()

    @classmethod
    def validate(cls, instance):
        must_not_be_present(
            fromCarePlanGroupId=instance.fromCarePlanGroupId,
            toCarePlanGroupId=instance.toCarePlanGroupId,
            createDateTime=instance.createDateTime,
            updateDateTime=instance.updateDateTime,
            id=instance.id,
        )

    def to_user(self) -> UpdateUserProfileRequestObject:
        user_data = {
            User.ID: self.userId,
            User.CARE_PLAN_GROUP_ID: self.carePlanGroupId,
        }
        return UpdateUserProfileRequestObject.from_dict(user_data)

    def to_care_plan_group_log(self) -> CarePlanGroupLog:
        now = datetime.utcnow()
        request_dict = self.to_dict(include_none=False)
        request_dict[CarePlanGroupLog.TO_CARE_PLAN_GROUP_ID] = self.carePlanGroupId
        request_dict[CarePlanGroupLog.CREATE_DATE_TIME] = now
        request_dict[CarePlanGroupLog.UPDATE_DATE_TIME] = now
        return CarePlanGroupLog.from_dict(request_dict)


@convertibleclass
class RetrieveUserCarePlanGroupLogRequestObject:
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"

    userId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveFullConfigurationRequestObject:
    USER = "user"

    user: AuthorizedUser = required_field()


@convertibleclass
class CreatePersonalDocumentRequestObject:
    NAME = "name"
    FILE_TYPE = "fileType"
    FILE_OBJECT = "fileObject"
    USER_ID = "userId"

    name: str = required_field(metadata=meta(validate_entity_name))
    fileType: PersonalDocument.PersonalDocumentMediaType = required_field()
    fileObject: S3Object = required_field()
    userId: str = required_field(metadata=meta(validate_object_id))

    def to_personal_document(self) -> PersonalDocument:
        data: dict = self.to_dict()
        data.pop(self.USER_ID)
        return PersonalDocument.from_dict(data)


@convertibleclass
class RetrievePersonalDocumentsRequestObject:
    USER_ID = "userId"
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class CreateHelperAgreementLogRequestObject(HelperAgreementLog):
    @classmethod
    def validate(cls, instance):
        must_not_be_present(
            createDateTime=instance.createDateTime,
            updateDateTime=instance.updateDateTime,
            id=instance.id,
        )


@convertibleclass
class RetrieveDeploymentConfigRequestObject:
    USER = "user"

    user: AuthorizedUser = default_field()


@convertibleclass
class RetrieveStaffRequestObject(RequestObject):
    ORGANIZATION_ID = "organizationId"
    NAME_CONTAINS = "nameContains"
    SUBMITTER = "submitter"

    nameContains: str = default_field()
    organizationId: str = required_field(metadata=meta(validate_object_id))
    submitter: AuthorizedUser = required_field()


@convertibleclass
class OffBoardUserRequestObject(RequestObject):
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"
    DETAILS_OFF_BOARDED = "detailsOffBoarded"
    DEPLOYMENT = "deployment"
    LANGUAGE = "language"

    userId: str = required_field(metadata=meta(validate_object_id))
    detailsOffBoarded: str = required_field(metadata=meta(validate_entity_name))
    deployment: Deployment = required_field()
    submitterId: str = required_field(metadata=meta(validate_object_id))
    language: str = default_field(metadata=meta(validate_language))

    def post_init(self):
        localization = self.deployment.get_localization(self.language)
        reverse_localization = {val: key for key, val in localization.items()}
        self.detailsOffBoarded = replace_values(
            self.detailsOffBoarded, reverse_localization
        )


@convertibleclass
class OffBoardUsersRequestObject(RequestObject):
    USER_IDS = "userIds"
    SUBMITTER_ID = "submitterId"
    DETAILS_OFF_BOARDED = "detailsOffBoarded"
    DEPLOYMENT = "deployment"
    LANGUAGE = "language"

    userIds: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    detailsOffBoarded: str = required_field(metadata=meta(validate_entity_name))
    submitterId: str = required_field(metadata=meta(validate_object_id))
    deployment: Deployment = required_field()
    language: str = default_field(metadata=meta(validate_language))

    @classmethod
    def validate(cls, request_object):
        must_not_be_empty_list(userIds=request_object.userIds)

    def post_init(self):
        localization = self.deployment.get_localization(self.language)
        reverse_localization = {val: key for key, val in localization.items()}
        self.detailsOffBoarded = replace_values(
            self.detailsOffBoarded, reverse_localization
        )


@convertibleclass
class ReactivateUserRequestObject(RequestObject):
    USER_ID = "userId"
    SUBMITTER_ID = "submitterId"

    userId: str = required_field(metadata=meta(validate_object_id))
    submitterId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class ReactivateUsersRequestObject(RequestObject):
    USER_IDS = "userIds"
    SUBMITTER_ID = "submitterId"
    DEPLOYMENT_ID = "deploymentId"

    userIds: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    deploymentId: str = required_field(metadata=meta(validate_object_id))
    submitterId: str = required_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, request_object):
        must_not_be_empty_list(userIds=request_object.userIds)


@convertibleclass
class SystemOffBoardUserRequestObject(RequestObject):
    USER_ID = "userId"
    REASON = "reason"

    userId: str = required_field(metadata=meta(validate_object_id))
    reason: BoardingStatus.ReasonOffBoarded = required_field()


@convertibleclass
class LinkProxyRequestObject:
    AUTHZ_USER = "authzUser"
    PROXY_EMAIL = "proxyEmail"

    authzUser: AuthorizedUser = required_field()
    proxyEmail: str = required_field(metadata=meta(validate_email))


@convertibleclass
class UnlinkProxyRequestObject:
    USER_ID = "userId"
    PROXY_ID = "proxyId"

    userId: str = required_field(metadata=meta(validate_object_id))
    proxyId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveProxyInvitationsRequestObject:
    SUBMITTER = "submitter"

    submitter: AuthorizedUser = required_field()


@convertibleclass
class RetrieveUserResourcesRequestObject:
    USER_ID = "userId"

    userId: str = required_field(metadata=meta(validate_object_id))
