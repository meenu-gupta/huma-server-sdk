from dataclasses import field

from isodate import parse_duration

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.router.invitation_request_objects import (
    validate_default_role_id,
)
from sdk import convertibleclass, meta
from sdk.auth.use_case.auth_request_objects import BaseAuthRequestObject
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_email_list,
    validate_object_id,
    must_be_present,
    not_empty,
)

INVITATION_PERMISSIONS_PER_ROLE: dict[str, list[str]] = {
    RoleName.SUPER_ADMIN: [
        RoleName.HUMA_SUPPORT,
        RoleName.ACCOUNT_MANAGER,
        RoleName.ORGANIZATION_OWNER,
        RoleName.ORGANIZATION_EDITOR,
    ],
    RoleName.HUMA_SUPPORT: [
        RoleName.ACCOUNT_MANAGER,
        RoleName.ORGANIZATION_OWNER,
        RoleName.ORGANIZATION_EDITOR,
    ],
    RoleName.ORGANIZATION_OWNER: [
        RoleName.ORGANIZATION_OWNER,
        RoleName.ORGANIZATION_EDITOR,
    ],
}


@convertibleclass
class SendAdminInvitationsRequestObject(BaseAuthRequestObject):
    ORGANIZATION_ID = "organizationId"
    EMAILS = "emails"
    ROLE_ID = "roleId"
    EXPIRES_IN = "expiresIn"
    SUBMITTER = "submitter"

    clientId: str = required_field(metadata=meta(not_empty))
    projectId: str = required_field(metadata=meta(not_empty))
    emails: list[str] = required_field(metadata=meta(validate_email_list))
    roleId: str = required_field(metadata=meta(validate_default_role_id))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    expiresIn: str = field(default="P1W", metadata=meta(parse_duration))
    submitter: AuthorizedUser = required_field()

    @classmethod
    def validate(cls, request_object: "SendAdminInvitationsRequestObject"):
        super().validate(request_object)
        if request_object.roleId != RoleName.ACCOUNT_MANAGER:
            must_be_present(organizatonId=request_object.organizationId)

        submitter_role = request_object.submitter.get_role()
        allowed_roles = INVITATION_PERMISSIONS_PER_ROLE.get(submitter_role.id) or []
        if request_object.roleId not in allowed_roles:
            raise PermissionDenied

    def post_init(self):
        if self.roleId == RoleName.ACCOUNT_MANAGER:
            self.organizationId = "*"
