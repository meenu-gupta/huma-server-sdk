from datetime import datetime

from isodate import parse_duration

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.models.invitation import Invitation
from extensions.authorization.models.user import RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.admin_invitation_request_objects import (
    SendAdminInvitationsRequestObject,
)
from extensions.authorization.router.invitation_response_objects import (
    SendInvitationsResponseObject,
)
from extensions.authorization.use_cases.invitation_use_cases import (
    INVITATION_TOKEN,
)
from extensions.exceptions import UserDoesNotExist
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig


class SendAdminInvitationsUseCase(UseCase):
    request_object = SendAdminInvitationsRequestObject
    created_ids = []
    not_updated_users = []

    @autoparams()
    def __init__(
        self,
        invitation_repo: InvitationRepository,
        invitation_adapter: EmailInvitationAdapter,
        token_adapter: TokenAdapter,
        server_config: PhoenixServerConfig,
        auth_repo: AuthorizationRepository,
        org_repo: OrganizationRepository,
    ):
        self._invitation_repo = invitation_repo
        self._invitation_adapter = invitation_adapter
        self._token_adapter = token_adapter
        self._config = server_config
        self._auth_repo = auth_repo
        self._org_repo = org_repo

    def execute(self, request_object: SendAdminInvitationsRequestObject):
        self.created_ids.clear()
        self.not_updated_users.clear()
        return super().execute(request_object)

    def process_request(self, request_object: SendAdminInvitationsRequestObject):
        org_name = None
        if request_object.organizationId and request_object.organizationId != "*":
            organization = self._org_repo.retrieve_organization(
                organization_id=request_object.organizationId
            )
            org_name = organization.name

        for email in self.request_object.emails:
            if self.invitation_should_be_sent(email):
                self._invite(email, org_name)
            else:
                self.not_updated_users.append(email)

        return SendInvitationsResponseObject(
            self.created_ids or None, self.not_updated_users or None
        )

    def _invite(self, email: str, organization_name: str):
        invitation = self._create_invitation(email)
        self._invitation_adapter.send_admin_invitation_email(
            invitation.email,
            self.request_object.roleId,
            self._super_admin_client,
            self.request_object.language,
            invitation.code,
            self.request_object.submitter.user.get_full_name(),
            organization_name,
        )

    def invitation_should_be_sent(self, email: str) -> bool:
        try:
            self._auth_repo.retrieve_simple_user_profile(email=email)
        except UserDoesNotExist:
            return True

        return False

    def _create_invitation(self, email: str):
        data = {
            Invitation.EMAIL: email,
            Invitation.CODE: self._create_invitation_token(email),
            Invitation.ROLES: [self._create_role_assignment()],
            Invitation.EXPIRES_AT: datetime.utcnow() + self.expires_in,
            Invitation.SENDER_ID: self.request_object.submitter.id,
            Invitation.CLIENT_ID: self._super_admin_client.id,
        }
        invitation = Invitation.from_dict(remove_none_values(data))
        invitation_id = self._invitation_repo.create_invitation(invitation)
        self.created_ids.append(invitation_id)
        return invitation

    def _create_invitation_token(self, identity: str) -> str:
        return self._token_adapter.create_token(
            identity, INVITATION_TOKEN, expires_delta=self.expires_in
        )

    def _create_role_assignment(self) -> RoleAssignment:
        return RoleAssignment.create_role(
            self.request_object.roleId, self.request_object.organizationId
        )

    @property
    def _super_admin_client(self) -> Client:
        project = self._config.server.project
        return project.get_client_by_client_type(Client.ClientType.ADMIN_WEB)

    @property
    def expires_in(self):
        return parse_duration(self.request_object.expiresIn)
