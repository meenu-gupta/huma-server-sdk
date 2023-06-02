from bson import ObjectId
from dataclasses import field
from typing import Optional

from aenum import Enum
from isodate import parse_duration

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.validators import (
    check_role_id_valid_for_organization,
    is_common_role,
)
from extensions.common.sort import SortField
from sdk.auth.use_case.auth_request_objects import BaseAuthRequestObject
from sdk.common.exceptions.exceptions import InvalidRequestException, PermissionDenied
from sdk.common.localization.utils import Language
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    positive_integer_field,
    default_field,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    validate_id,
    validate_email_list,
    validate_object_id,
    validate_object_ids,
    must_be_present,
    must_not_be_present,
    validate_email,
    incorrect_language_to_default,
    must_be_at_least_one_of,
    not_empty,
)
from sdk.phoenix.config.server_config import Client

INVITATION_PERMISSIONS_PER_ROLE: dict[str, list[str]] = {
    RoleName.ADMINISTRATOR: [
        RoleName.ADMINISTRATOR,
        RoleName.CLINICIAN,
        RoleName.SUPERVISOR,
        RoleName.SUPPORT,
        RoleName.USER,
    ],
    RoleName.CLINICIAN: [RoleName.USER, RoleName.PROXY],
}


def validate_role_id(field_value: str) -> bool:
    if validate_default_role_id(field_value):
        return True
    if validate_id(field_value):
        return True
    return False


@autoparams("default_roles")
def validate_default_role_id(value: str, default_roles: DefaultRoles) -> bool:
    return value in default_roles


@convertibleclass
class SendInvitationRequestObject(RequestObject):
    INVITATION = "invitation"
    CLIENT = "client"
    SENDER = "sender"
    LANGUAGE = "language"
    EXTRA_INFO = "extraInfo"

    invitation: Invitation = required_field()
    client: Client = required_field()
    sender: AuthorizedUser = required_field()
    language: str = field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )
    extraInfo: dict = default_field()


@convertibleclass
class SendInvitationsRequestObject(BaseAuthRequestObject):
    DEPLOYMENT_IDS = "deploymentIds"
    ORGANIZATION_ID = "organizationId"
    EMAILS = "emails"
    ROLE_ID = "roleId"
    PATIENT_ID = "patientId"
    EXPIRES_IN = "expiresIn"
    SUBMITTER = "submitter"

    emails: list[str] = required_field(metadata=meta(validate_email_list))
    roleId: str = required_field(metadata=meta(validate_role_id))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    patientId: str = default_field(metadata=meta(validate_object_id))
    expiresIn: str = field(default="P1W", metadata=meta(parse_duration))
    submitter: AuthorizedUser = required_field()

    @classmethod
    def validate(cls, instance):
        super().validate(instance)
        is_org_role = check_role_id_valid_for_organization(
            instance.roleId, instance.organizationId
        )
        is_proxy_role = instance.roleId == RoleName.PROXY
        is_common_role = instance.roleId in RoleName.common_roles()
        if is_common_role:
            must_be_at_least_one_of(
                organizationId=instance.organizationId,
                deploymentIds=instance.deploymentIds,
            )
            must_not_be_present(patientId=instance.patientId)

            if instance.deploymentIds and len(instance.deploymentIds) > 1:
                must_be_present(organizationId=instance.organizationId)
        elif is_org_role:
            must_be_present(organizationId=instance.organizationId)
            must_not_be_present(deploymentIds=instance.deploymentIds)
            must_not_be_present(patientId=instance.patientId)
        elif is_proxy_role:
            must_be_present(patientId=instance.patientId)
            must_not_be_present(deploymentIds=instance.deploymentIds)
            must_not_be_present(organizationId=instance.organizationId)
        else:
            must_not_be_present(patientId=instance.patientId)
            must_be_present(deploymentIds=instance.deploymentIds)
            if len(instance.deploymentIds) == 0:
                msg = f"Must be invited to at least one deployment"
                raise InvalidRequestException(msg)

            multiple_deployment_role = (
                instance.roleId in cls.multiple_deployment_roles()
            )

            if multiple_deployment_role and len(instance.deploymentIds) > 1:
                must_be_present(organizationId=instance.organizationId)

            if not multiple_deployment_role and len(instance.deploymentIds) > 1:
                msg = f"Role {instance.roleId} can only be invited to one deployment"
                raise InvalidRequestException(msg)

    def check_permission(self, submitter: AuthorizedUser):
        submitter_role = submitter.get_role()

        if submitter.is_super_admin():
            return

        if is_common_role(submitter_role.id):
            if not self.roleId == RoleName.PROXY:
                if not submitter.role_assignment.is_org():
                    if not self.deploymentIds:
                        raise PermissionDenied
                    else:
                        self.validate_resource_access(
                            "deployment", self.deploymentIds, submitter
                        )
                else:
                    if self.deploymentIds:
                        self.validate_resource_access(
                            "deployment", self.deploymentIds, submitter
                        )
                    elif self.organizationId:
                        self.validate_resource_access(
                            "organization", [self.organizationId], submitter
                        )

            allowed_roles = INVITATION_PERMISSIONS_PER_ROLE.get(submitter_role.id) or []
            if ObjectId.is_valid(self.roleId):
                allowed_roles.append(self.roleId)
            if self.roleId not in allowed_roles:
                raise PermissionDenied

    @staticmethod
    def validate_resource_access(
        resource_name: str, resources: list[str], submitter: AuthorizedUser
    ):
        allowed_resources = []

        if resource_name == "organization":
            allowed_resources = submitter.organization_ids()
        elif resource_name == "deployment":
            allowed_resources = submitter.deployment_ids()

        if not all(resource_id in allowed_resources for resource_id in resources):
            raise PermissionDenied

    @staticmethod
    def multiple_deployment_roles():
        org_keys = inject.instance(DefaultRoles).organization.keys()
        return (set(org_keys) - set(RoleName.org_roles())).union(
            set(RoleName.common_roles())
        )

    @property
    def deployment_id(self) -> Optional[str]:
        if self.deploymentIds:
            return self.deploymentIds[0]


@convertibleclass
class ResendInvitationsRequestObject(BaseAuthRequestObject):
    INVITATION_CODE = "invitationCode"
    EMAIL = "email"

    email: str = required_field(metadata=meta(validate_email))
    invitationCode: str = required_field()


@convertibleclass
class ResendInvitationsListRequestObject(BaseAuthRequestObject):
    INVITATIONS_LIST = "invitationsList"

    @convertibleclass
    class InvitationItem:
        INVITATION_CODE = "invitationCode"
        EMAIL = "email"

        email: str = required_field(metadata=meta(validate_email))
        invitationCode: str = required_field(metadata=meta(not_empty))

    invitationsList: list[InvitationItem] = required_field(metadata=meta(not_empty))


@convertibleclass
class GetInvitationLinkRequestObject(BaseAuthRequestObject):
    DEPLOYMENT_ID = "deploymentId"
    ROLE_ID = "roleId"
    EXPIRES_IN = "expiresIn"
    RETRIEVE_SHORTENED = "retrieveShortened"
    SENDER_ID = "senderId"

    deploymentId: str = required_field()
    roleId: str = required_field()
    expiresIn: str = field(default="P1W", metadata=meta(parse_duration))
    retrieveShortened: bool = field(default=False)
    senderId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteInvitationRequestObject(RequestObject):
    INVITATION_ID = "invitationId"

    invitationId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteInvitationsListRequestObject(RequestObject):
    INVITATION_ID_LIST = "invitationIdList"
    INVITATION_TYPE = "invitationType"

    invitationIdList: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_object_id, x)))
    )
    invitationType: InvitationType = field(default=InvitationType.PERSONAL)


@convertibleclass
class RetrieveInvitationsRequestObject(BaseAuthRequestObject):
    EMAIL = "email"
    ROLE_TYPE = "roleType"
    SKIP = "skip"
    LIMIT = "limit"
    SUBMITTER = "submitter"
    INVITATION_TYPE = "invitationType"
    SORT_FIELDS = "sortFields"

    class RoleType(Enum):
        MANAGER = "Manager"
        USER = "User"

    email: str = default_field()
    roleType: RoleType = required_field()
    skip: int = positive_integer_field(default=None, metadata=meta(required=True))
    limit: int = positive_integer_field(default=None, metadata=meta(required=True))
    submitter: AuthorizedUser = required_field()
    invitationType: InvitationType = default_field()
    sortFields: list[SortField] = default_field()

    def post_init(self):
        if not self.sortFields:
            self.sortFields = [
                SortField.from_dict(
                    {
                        SortField.FIELD: Invitation.CREATE_DATE_TIME,
                        SortField.DIRECTION: SortField.Direction.DESC.value,
                    }
                )
            ]


@convertibleclass
class InvitationValidityRequestObject(RequestObject):
    INVITATION_CODE = "invitationCode"

    invitationCode: str = required_field()
