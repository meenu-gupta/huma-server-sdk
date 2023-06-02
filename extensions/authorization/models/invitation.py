from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Optional

from extensions.authorization.models.user import RoleAssignment
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_email,
    validate_id,
    default_datetime_meta,
    validate_shortened_invitation_code,
)


class InvitationType(Enum):
    PERSONAL = "PERSONAL"
    UNIVERSAL = "UNIVERSAL"


@convertibleclass
class Invitation:
    ID_ = "_id"
    CODE = "code"
    SHORTENED_CODE = "shortenedCode"
    EMAIL = "email"
    STATUS = "status"
    ID = "id"
    ROLES = "roles"
    NUMBER_OF_TRY = "numberOfTry"
    EXPIRES_AT = "expiresAt"
    TYPE = "type"
    CREATE_DATE_TIME = "createDateTime"
    # these are needed for proper resending
    SENDER_ID = "senderId"
    CLIENT_ID = "clientId"
    EXTRA_INFO = "extraInfo"
    INVITATION_TYPE = "type"

    VALID_SORT_FIELDS = [
        CREATE_DATE_TIME,
    ]

    id: str = default_field(metadata=meta(validate_id))
    email: str = default_field(metadata=meta(validate_email))
    code: str = required_field()
    shortenedCode: str = default_field(
        metadata=meta(validate_shortened_invitation_code)
    )
    roles: list[RoleAssignment] = default_field()
    numberOfTry: int = field(default=1)
    type: InvitationType = field(default=InvitationType.PERSONAL)
    expiresAt: datetime = required_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    senderId: str = default_field(metadata=meta(validate_id))
    clientId: str = default_field()
    extraInfo: dict = default_field()

    @property
    def role_id(self) -> Optional[str]:
        """Get the first invitation roleId as a reference"""
        return self.role and self.role.roleId

    @property
    def role(self) -> Optional[RoleAssignment]:
        """Get the first invitation role as a reference"""
        return self.roles and self.roles[0]

    @property
    def is_universal(self):
        return self.type == InvitationType.UNIVERSAL
