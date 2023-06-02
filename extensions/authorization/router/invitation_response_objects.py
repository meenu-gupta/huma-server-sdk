from dataclasses import field

from extensions.authorization.models.invitation import Invitation
from sdk import convertibleclass
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import (
    positive_integer_field,
    meta,
    default_field,
)
from sdk.common.utils.validators import validate_entity_name


class SendInvitationsResponseObject(response_object.Response):
    ALREADY_SIGNED_UP_EMAILS = "alreadySignedUpEmails"

    @convertibleclass
    class Response:
        alreadySignedUpEmails: list[str] = default_field()
        ids: list[str] = default_field()
        ok: bool = field(default=True)

    def __init__(
        self,
        ids: list[str],
        already_signed_up_emails: list[str] = None,
        result: bool = True,
    ):
        super().__init__(
            value=self.Response(
                alreadySignedUpEmails=already_signed_up_emails, ok=result, ids=ids
            )
        )


class ResendInvitationsResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        ok: bool = field(default=True)

    def __init__(
        self,
        result: bool = True,
    ):
        super().__init__(
            value=self.Response(
                ok=result,
            )
        )


class GetInvitationLinkResponseObject(response_object.Response):
    LINK = "link"
    INVITATION_CODE = "invitationCode"
    SHORTENED_CODE = "shortenedCode"

    @convertibleclass
    class Response:
        link: str = default_field()

    def __init__(self, link: str):
        super().__init__(
            value=self.Response(
                link=link,
            )
        )


@convertibleclass
class InvitationResponseModel(Invitation):
    ROLE_NAME = "roleName"
    INVITATION_LINK = "invitationLink"
    INVITED_BY = "invitedBy"

    roleName: str = default_field(metadata=meta(validate_entity_name))
    invitationLink: str = default_field()
    invitedBy: str = default_field()


class RetrieveInvitationsResponseObject(response_object.Response):
    INVITATIONS = "invitations"

    @convertibleclass
    class Response:
        invitations: list[Invitation] = default_field()
        total: int = positive_integer_field(default=None)
        limit: int = positive_integer_field(default=None)
        skip: int = positive_integer_field(default=None)

    def __init__(
        self, invitations: list[Invitation], total: int, limit: int, skip: int
    ):
        super().__init__(
            value=self.Response(
                invitations=invitations, total=total, limit=limit, skip=skip
            )
        )


class RetrieveInvitationsV1ResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        invitations: list[Invitation] = field(default=None)
        filtered: int = positive_integer_field(default=None)
        total: int = positive_integer_field(default=None)

    def __init__(
        self,
        invitations: list[Invitation],
        filtered: int,
        total: int,
    ):
        super().__init__(
            value=self.Response(
                invitations=invitations,
                filtered=filtered,
                total=total,
            )
        )


class InvitationValidityResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        ok: bool = field(default=True)
        invitationCode: str = field(default=None)

    def __init__(
        self,
        code: str,
        valid: bool = True,
    ):
        super().__init__(
            value=self.Response(
                invitationCode=code,
                ok=valid,
            )
        )


class ResendInvitationsListResponse(response_object.Response):
    @convertibleclass
    class Response:
        resentInvitations: int = field(default=0)

    def __init__(
        self,
        resent_invitations: int,
    ):
        super().__init__(
            value=self.Response(
                resentInvitations=resent_invitations,
            )
        )


class DeleteInvitationsListResponse(response_object.Response):
    @convertibleclass
    class Response:
        deletedInvitations: int = field(default=0)

    def __init__(
        self,
        deleted_invitations: int,
    ):
        super().__init__(
            value=self.Response(
                deletedInvitations=deleted_invitations,
            )
        )
