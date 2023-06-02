import functools
from abc import ABC
from datetime import datetime, timedelta

import isodate
import pytz
from dateutil.relativedelta import relativedelta

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.exceptions import CantResendInvitation
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    ResendInvitationsRequestObject,
    RetrieveInvitationsRequestObject,
    DeleteInvitationRequestObject,
    GetInvitationLinkRequestObject,
    SendInvitationRequestObject,
    ResendInvitationsListRequestObject,
)
from extensions.authorization.router.invitation_response_objects import (
    SendInvitationsResponseObject,
    RetrieveInvitationsResponseObject,
    RetrieveInvitationsV1ResponseObject,
    InvitationResponseModel,
    GetInvitationLinkResponseObject,
    DeleteInvitationsListResponse,
    ResendInvitationsListResponse,
)
from extensions.authorization.router.user_profile_request import AddRolesRequestObject
from extensions.authorization.services.authorization import AuthorizationService
from extensions.authorization.use_cases.add_role_use_case import AddRolesUseCase
from extensions.authorization.validators import (
    check_role_id_valid_for_organization,
    is_common_role,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.exceptions import UserDoesNotExist
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.auth.use_case.auth_use_cases import get_client
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    InvalidRoleException,
    InvalidRequestException,
    ObjectDoesNotExist,
    InvalidShortInvitationCodeException,
    PermissionDenied,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    remove_none_values,
    utc_str_field_to_val,
    validate_shortened_invitation_code,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client

INVITATION_TOKEN = "invitation"
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


@autoparams("invitation_repo", "token_adapter")
def retrieve_invitation(
    invitation_repo: InvitationRepository,
    token_adapter: TokenAdapter,
    invitation_code: str = None,
    shortened_invitation_code: str = None,
) -> Invitation:
    invitation = None
    if invitation_code:
        token_adapter.verify_invitation_token(token=invitation_code)
        invitation = invitation_repo.retrieve_invitation(code=invitation_code)
    elif shortened_invitation_code:
        if not validate_shortened_invitation_code(shortened_invitation_code):
            raise InvalidShortInvitationCodeException
        invitation = invitation_repo.retrieve_invitation(
            shortened_code=shortened_invitation_code
        )
    return invitation


@autoparams("invitation_repo")
def delete_invitation(invitation_id, invitation_repo: InvitationRepository):
    invitation_repo.delete_invitation(invitation_id=invitation_id)


class CommonInvitationUseCase(UseCase, ABC):
    @autoparams()
    def __init__(
        self,
        invitation_repo: InvitationRepository,
        invitation_adapter: EmailInvitationAdapter,
        token_adapter: TokenAdapter,
        server_config: PhoenixServerConfig,
        deployment_repo: DeploymentRepository,
        auth_repo: AuthorizationRepository,
        organization_repo: OrganizationRepository,
        default_roles: DefaultRoles,
    ):
        self._invitation_repo = invitation_repo
        self._invitation_adapter = invitation_adapter
        self._token_adapter = token_adapter
        self._config = server_config
        self._deployment_repo = deployment_repo
        self._auth_repo = auth_repo
        self._organization_repo = organization_repo
        self._default_roles = default_roles

    def get_custom_role_or_raise_error(self, role_assignment: RoleAssignment) -> Role:
        if role_assignment.is_deployment() and role_assignment.resource_id():
            resource = self._deployment_repo.retrieve_deployment(
                deployment_id=role_assignment.resource_id()
            )
        elif role_assignment.is_org() and role_assignment.resource_id():
            resource = self._organization_repo.retrieve_organization(
                organization_id=role_assignment.resource_id()
            )
        else:
            msg = f"role assignment {role_assignment} is not valid"
            raise InvalidRequestException(msg)

        if not (role := resource.find_role_by_id(role_assignment.roleId)):
            raise InvalidRoleException

        return role

    def _get_policy_populated_with_deployment_data(self, deployment_id: str):
        deployment = self._deployment_repo.retrieve_deployment(
            deployment_id=deployment_id
        )
        return {
            Deployment.PRIVACY_POLICY_URL: deployment.privacyPolicyUrl,
            Deployment.EULA_URL: deployment.eulaUrl,
            Deployment.TERM_AND_CONDITION_URL: deployment.termAndConditionUrl,
        }

    def _get_valid_client_for_user_invitation(self):
        valid_client_ids = (Client.ClientType.USER_IOS, Client.ClientType.USER_ANDROID)
        clients = self._config.server.project.clients
        if client := find(lambda c: c.clientType in valid_client_ids, clients):
            return client

        raise InvalidRequestException("No valid user client")

    def _send_invitation_email(
        self,
        invitation: Invitation,
        client: Client,
        submitter: AuthorizedUser,
        language: str,
    ):
        data = {
            SendInvitationRequestObject.INVITATION: invitation,
            SendInvitationRequestObject.SENDER: submitter,
            SendInvitationRequestObject.CLIENT: client,
            SendInvitationRequestObject.LANGUAGE: language,
        }
        request_obj = SendInvitationRequestObject.from_dict(data)
        use_case = SendInvitationUseCase(
            invitation_repo=self._invitation_repo,
            invitation_adapter=self._invitation_adapter,
            token_adapter=self._token_adapter,
            server_config=self._config,
            deployment_repo=self._deployment_repo,
            auth_repo=self._auth_repo,
            organization_repo=self._organization_repo,
        )
        use_case.execute(request_obj)


class SendInvitationUseCase(CommonInvitationUseCase):
    def process_request(self, request_object: SendInvitationRequestObject):
        role = self._get_role(request_object.invitation)
        client = self._get_client(role)
        sender = request_object.sender.user
        if role.userType == Role.UserType.USER:
            self._invitation_adapter.send_user_invitation_email(
                self.request_object.invitation.email,
                client,
                request_object.language,
                request_object.invitation.code,
            )
        elif role.userType == Role.UserType.PROXY:
            extras = request_object.invitation.extraInfo or {}
            self._invitation_adapter.send_proxy_invitation_email(
                request_object.invitation.email,
                request_object.language,
                client,
                request_object.invitation.code,
                sender.get_full_name(),
                **extras,
            )
        else:
            self._invitation_adapter.send_invitation_email(
                request_object.invitation.email,
                role.name,
                client,
                request_object.language,
                request_object.invitation.code,
                sender.get_full_name(),
            )

    def _get_client(self, role: Role) -> Client:
        if role.userType in (Role.UserType.USER, Role.UserType.PROXY):
            return self._get_valid_client_for_user_invitation()
        return self.request_object.client

    def _get_role(self, invitation: Invitation) -> Role:
        default_roles = inject.instance(DefaultRoles)
        role = default_roles.get(invitation.role_id)
        if role:
            return role

        if len(invitation.roles) > 1:
            msg = "Custom role cannot be assigned to multiple resources"
            raise InvalidRoleException(msg)

        return self.get_custom_role_or_raise_error(invitation.role)


class SendInvitationsUseCase(CommonInvitationUseCase):
    client: Client = None
    role: Role = None
    role_assignments: list[RoleAssignment] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.not_updated_users = []
        self.created_ids = []

    def execute(self, request_object: SendInvitationsRequestObject):
        if request_object.roleId in self._default_roles.super_admins:
            raise InvalidRoleException

        self.request_object = request_object
        self.role = self.get_role()
        self.role_assignments = self._create_role_assignments(self.role.id)
        self.client = get_client(self._config.server.project, request_object.clientId)
        return super(SendInvitationsUseCase, self).execute(request_object)

    def get_role(self):
        role_id = self.request_object.roleId
        default_roles = inject.instance(DefaultRoles)
        if role := default_roles.get(self.request_object.roleId):
            return role

        if self.request_object.deploymentIds:
            if len(self.request_object.deploymentIds) > 1:
                msg = "Custom role cannot be assigned to multiple deployments"
                raise InvalidRoleException(msg)

            deployment = self._deployment_repo.retrieve_deployment(
                deployment_id=self.request_object.deploymentIds[0]
            )
            role = deployment.find_role_by_id(role_id)
            if not role and not self.request_object.organizationId:
                raise InvalidRoleException

        if self.request_object.organizationId:
            organization = self._organization_repo.retrieve_organization(
                organization_id=self.request_object.organizationId
            )
            role = organization.find_role_by_id(role_id)
            if not role:
                raise InvalidRoleException

        return role

    def process_request(self, _) -> SendInvitationsResponseObject:
        if self.request_object.patientId:
            self.request_object.expiresIn = "P1D"
            self.proxy_check_already_pending_invite(self.request_object.patientId)

        self.send_emails()
        return SendInvitationsResponseObject(
            self.created_ids or None, self.not_updated_users or None
        )

    def send_emails(self):
        expiration = isodate.parse_duration(self.request_object.expiresIn)
        for email in self.request_object.emails:
            if self.invitation_should_be_sent(email):
                invitation = self._create_invitation(email, expiration)
                self._send_invitation_email(
                    invitation,
                    self.client,
                    self.request_object.submitter,
                    self.request_object.language,
                )

    def invitation_should_be_sent(self, email) -> bool:
        try:
            user = self._auth_repo.retrieve_simple_user_profile(email=email)
        except UserDoesNotExist:
            return True

        if not user.roles:
            self._assign_role_to_user(user, self.role_assignments)
            self.send_role_update_email(user.id)
            return False

        self.not_updated_users.append(email)
        return False

    def _create_invitation(self, email, expiration):
        created_at = datetime.utcnow()
        policy_data = self._get_policy_data_based_on_role(
            self.role,
            self.request_object.deploymentIds,
            self.request_object.organizationId,
            self.request_object.patientId,
        )
        user_claims = remove_none_values(
            {
                **policy_data,
                self._config.server.COUNTRY_CODE: self._config.server.countryCode,
                Invitation.CREATE_DATE_TIME: utc_str_field_to_val(created_at),
            }
        )
        code = self._token_adapter.create_token(
            identity=email,
            token_type=INVITATION_TOKEN,
            expires_delta=expiration,
            user_claims=user_claims,
        )

        data = {
            Invitation.EMAIL: email,
            Invitation.CODE: code,
            Invitation.ROLES: self.role_assignments,
            Invitation.EXPIRES_AT: created_at + expiration,
            Invitation.SENDER_ID: self.request_object.submitter.id,
            Invitation.CLIENT_ID: self.client.clientId,
            Invitation.EXTRA_INFO: self._build_extras(),
        }
        invitation = Invitation.from_dict(remove_none_values(data))
        invitation_id = self._invitation_repo.create_invitation(invitation)
        self.created_ids.append(invitation_id)
        invitation.id = invitation_id
        return invitation

    def _get_policy_data_based_on_role(
        self,
        role: Role,
        deployment_ids: list[str],
        organization_id: str,
        patient_id: str,
    ) -> dict:
        is_deployment_or_call_center_role = role.name in (
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
        )

        if deployment_ids and len(deployment_ids) == 1:
            return self._policy_populated_with_deployment_data(deployment_ids[0])
        elif deployment_ids and len(deployment_ids) > 1:
            if is_deployment_or_call_center_role or is_common_role(role.id):
                organization_ids = self._organization_repo.retrieve_organization_ids(
                    deployment_ids
                )
                if (not organization_ids or len(organization_ids) > 1) or (
                    organization_ids[0] != organization_id
                ):
                    raise PermissionDenied

                return self._policy_populated_with_organization_data(organization_id)

        if check_role_id_valid_for_organization(role.id, organization_id):
            return self._policy_populated_with_organization_data(organization_id)

        if role.name == RoleName.PROXY:
            return self._policy_populated_with_proxy_data(patient_id)

        return self._policy_populated_with_deployment_data(deployment_ids[0])

    def _build_extras(self) -> dict:
        """
        Returns extra parameters that will be saved part of the invitation object
        """
        extras = {}
        if patient_id := self.request_object.patientId:
            dependant = self._get_dependant(patient_id)
            extras["dependant"] = dependant.givenName
        return extras

    def _get_dependant(self, dependant_id: str) -> User:
        submitter = self.request_object.submitter
        if submitter and submitter.id == dependant_id:
            return self.request_object.submitter.user

        try:
            return self._auth_repo.retrieve_simple_user_profile(user_id=dependant_id)
        except UserDoesNotExist:
            raise InvalidRequestException("Wrong patient id")

    @functools.lru_cache(maxsize=1)
    def _policy_populated_with_proxy_data(self, patient_id: str):
        dependant = self._get_dependant(patient_id)
        return self._policy_populated_with_deployment_data(
            dependant.roles[0].resource_id()
        )

    @functools.lru_cache(maxsize=1)
    def _policy_populated_with_deployment_data(self, deployment_id: str):
        deployment = self._deployment_repo.retrieve_deployment(
            deployment_id=deployment_id
        )
        return {
            Deployment.PRIVACY_POLICY_URL: deployment.privacyPolicyUrl,
            Deployment.EULA_URL: deployment.eulaUrl,
            Deployment.TERM_AND_CONDITION_URL: deployment.termAndConditionUrl,
        }

    @functools.lru_cache(maxsize=1)
    def _policy_populated_with_organization_data(self, organization_id: str):
        organization = self._organization_repo.retrieve_organization(
            organization_id=organization_id
        )
        return {
            Organization.PRIVACY_POLICY_URL: organization.privacyPolicyUrl,
            Organization.EULA_URL: organization.eulaUrl,
            Organization.TERM_AND_CONDITION_URL: organization.termAndConditionUrl,
        }

    def send_role_update_email(self, user_id: str):
        user = self._auth_repo.retrieve_simple_user_profile(user_id=user_id)
        deployments = AuthorizedUser(user).deployment_ids()
        self._invitation_adapter.send_role_update_email(
            to=user.email,
            client=self.client,
            locale=self.request_object.language,
            sender=self.request_object.submitter.user.get_full_name(),
            deployment_count=len(deployments),
        )

    @property
    def resource_ids(self):
        if is_common_role(self.request_object.roleId):
            if self.request_object.deploymentIds:
                resource_ids = self.request_object.deploymentIds
            elif self.request_object.organizationId:
                resource_ids = [self.request_object.organizationId]
        elif check_role_id_valid_for_organization(
            self.request_object.roleId, self.request_object.organizationId
        ):
            resource_ids = [self.request_object.organizationId]
        elif self.request_object.roleId == RoleName.PROXY:
            resource_ids = [self.request_object.patientId]
        else:
            resource_ids = self.request_object.deploymentIds
        return resource_ids

    def _assign_role_to_user(self, user: User, roles: list[RoleAssignment]) -> None:
        roles = [r.to_dict() for r in roles]
        body = {
            AddRolesRequestObject.ROLES: roles,
            AddRolesRequestObject.SUBMITTER: self.request_object.submitter,
            AddRolesRequestObject.USER_ID: user.id,
        }
        req_ob = AddRolesRequestObject.from_dict(body)
        use_case = AddRolesUseCase(
            self._auth_repo, self._deployment_repo, self._organization_repo
        )
        use_case.execute(req_ob)

    def _create_role_assignments(self, role_id: str) -> list[RoleAssignment]:
        if role_id == RoleName.PROXY:
            dependant_id = self.resource_ids[0]
            dependant = self._get_dependant(dependant_id)
            return [
                RoleAssignment.create_proxy(dependant.id),
                RoleAssignment.create_role(
                    RoleName.PROXY, dependant.roles[0].resource_id()
                ),
            ]

        resource_name = None
        if self.request_object.deploymentIds:
            resource_name = RoleAssignment.DEPLOYMENT
        elif self.request_object.organizationId:
            resource_name = RoleAssignment.ORGANIZATION

        return [
            RoleAssignment.create_role(role_id, resource_id, resource_name)
            for resource_id in self.resource_ids
        ]

    def proxy_check_already_pending_invite(self, user_id: str):
        try:
            invitation = self._invitation_repo.retrieve_proxy_invitation(user_id)
            if invitation:
                raise InvalidRequestException(
                    "There is an already pending proxy invitation"
                )
        except ObjectDoesNotExist:
            pass


class ResendInvitationsUseCase(CommonInvitationUseCase):
    def process_request(self, request_object: ResendInvitationsRequestObject):
        invitation = self._get_invitation_object()
        if not self._can_resend_invitation(invitation):
            raise CantResendInvitation(f"Re-sent quantity has exceeded the limit")
        client = self._get_initial_client(invitation)
        submitter = self._get_initial_submitter(invitation)
        self._send_invitation_email(
            invitation, client, submitter, request_object.language
        )
        invitation.numberOfTry += 1
        self._invitation_repo.update_invitation(invitation)

    def _can_resend_invitation(self, invitation: Invitation) -> bool:
        return (
            invitation.numberOfTry
            <= self._config.server.invitation.maxInvitationResendTimes
        )

    def _get_invitation_object(self) -> Invitation:
        invitation = self._invitation_repo.retrieve_invitation(
            code=self.request_object.invitationCode
        )
        if invitation.email and invitation.email != self.request_object.email:
            raise InvalidRequestException("Invalid email or invitation code")
        return invitation

    def _get_invitation_object_list(self) -> list[Invitation]:
        invitation_list = self._invitation_repo.retrieve_invitation_list_by_code_list(
            code_list=[
                invitation.invitationCode
                for invitation in self.request_object.invitationsList
            ]
        )
        return invitation_list

    def _validate_invitation_list(self, invitation_list):
        email_list = [
            invitation.email for invitation in self.request_object.invitationsList
        ]
        for invitation in invitation_list:
            if invitation.email and invitation.email not in email_list:
                raise InvalidRequestException("Invalid email or invitation code")

    def _get_initial_client(self, invitation: Invitation):
        # might be not present as old invitation objects had none
        if invitation.clientId:
            return get_client(self._config.server.project, invitation.clientId)

    def _get_initial_submitter(self, invitation: Invitation):
        # might be not present as old invitation objects had none
        if invitation.senderId:
            user = self._auth_repo.retrieve_user(user_id=invitation.senderId)
            return AuthorizedUser(user)


class ResendInvitationsListUseCase(ResendInvitationsUseCase):
    def process_request(
        self, request_object: ResendInvitationsListRequestObject
    ) -> ResendInvitationsListResponse:
        invitation_list = self._get_invitation_object_list()
        self._validate_invitation_list(invitation_list)
        for invitation in invitation_list:
            if not self._can_resend_invitation(invitation):
                raise CantResendInvitation(f"Re-sent quantity has exceeded the limit")
        for invitation in invitation_list:
            client = self._get_initial_client(invitation)
            submitter = self._get_initial_submitter(invitation)
            self._send_invitation_email(
                invitation, client, submitter, request_object.language
            )
            invitation.numberOfTry += 1
            self._invitation_repo.update_invitation(invitation)
        return ResendInvitationsListResponse(resent_invitations=len(invitation_list))


class GetInvitationLinkUseCase(CommonInvitationUseCase):
    def process_request(self, request_object: GetInvitationLinkRequestObject):
        get_client(self._config.server.project, self.request_object.clientId)

        allowed_roles = (Role.UserType.USER,)  # for now only user invitations allowed
        if self.request_object.roleId not in allowed_roles:
            raise InvalidRoleException

        delta = isodate.parse_duration(request_object.expiresIn)
        expires_at = datetime.utcnow() + delta
        invitation = self.get_existing_invitation(expires_at)
        retrieve_shortened = request_object.retrieveShortened

        if invitation:
            invitation_code = (
                invitation.shortenedCode if retrieve_shortened else invitation.code
            )
            return GetInvitationLinkResponseObject(
                self._build_link(
                    code=invitation_code, retrieve_shortened=retrieve_shortened
                )
            )

        invitation = self.create_new_invitation(
            expires_at, delta, request_object.senderId
        )
        invitation_code = (
            invitation.shortenedCode if retrieve_shortened else invitation.code
        )
        # link with base url of first available client
        return GetInvitationLinkResponseObject(
            self._build_link(
                code=invitation_code, retrieve_shortened=retrieve_shortened
            )
        )

    def _build_link(self, code: str, retrieve_shortened: bool):
        client = self._get_valid_client_for_user_invitation()
        button_link = self._config.server.project.notFoundLink
        code_query_param = "shortenedCode" if retrieve_shortened else "invitationCode"
        query_params = "{param}={code}".format(param=code_query_param, code=code)

        if client.deepLinkBaseUrl:
            button_link = "{base_url}/signup?{query}".format(
                base_url=client.deepLinkBaseUrl, query=query_params
            )
        return button_link

    def create_new_invitation(
        self, expires_at: datetime, delta: timedelta, submitter_id: str
    ) -> Invitation:
        policy_data = self._get_policy_populated_with_deployment_data(
            self.request_object.deploymentId
        )
        user_claims = remove_none_values(
            {
                **policy_data,
                self._config.server.COUNTRY_CODE: self._config.server.countryCode,
            }
        )
        code = self._token_adapter.create_token(
            token_type=INVITATION_TOKEN,
            expires_delta=delta,
            user_claims=user_claims,
        )
        role = RoleAssignment.create_role(
            self.request_object.roleId, self.request_object.deploymentId
        )
        data = {
            Invitation.ROLES: [role],
            Invitation.EXPIRES_AT: expires_at,
            Invitation.CODE: code,
            Invitation.TYPE: InvitationType.UNIVERSAL.value,
            Invitation.SENDER_ID: submitter_id,
        }
        new_invitation = Invitation.from_dict(data)
        self._invitation_repo.create_invitation(new_invitation)
        return new_invitation

    def get_existing_invitation(self, expires_at: datetime):
        utc_tz = pytz.timezone("UTC")
        expires_from = expires_at.replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=utc_tz
        )
        expires_till = expires_from + relativedelta(days=1)
        try:
            invitation = self._invitation_repo.retrieve_universal_invitation(
                deployment_id=self.request_object.deploymentId,
                role_id=self.request_object.roleId,
                expires_from=expires_from,
                expires_till=expires_till,
            )
        except ObjectDoesNotExist:
            return
        return invitation


class DeleteInvitationUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: InvitationRepository):
        self._repo = repo

    def process_request(self, request_object: DeleteInvitationRequestObject):
        self._repo.delete_invitation(invitation_id=request_object.invitationId)


class DeleteInvitationsListUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: InvitationRepository):
        self._repo = repo

    def process_request(
        self, request_object: DeleteInvitationRequestObject
    ) -> DeleteInvitationsListResponse:
        return DeleteInvitationsListResponse(
            self._repo.delete_invitation_list(
                invitation_id_list=request_object.invitationIdList,
                invitation_type=request_object.invitationType,
            )
        )


class RetrieveInvitationsUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: InvitationRepository, default_roles: DefaultRoles):
        self._repo = repo
        self._default_roles = default_roles

    def process_request(self, request_object: RetrieveInvitationsRequestObject):
        role_ids = self._get_role_ids()
        invitations, total = self._repo.retrieve_invitations(
            email=request_object.email,
            skip=request_object.skip,
            limit=request_object.limit,
            role_ids=role_ids,
            deployment_id=request_object.submitter.deployment_id(),
            organization_id=request_object.submitter.organization_id(),
        )

        invitations = self._convert_invitations_to_resp_objects(invitations)

        return RetrieveInvitationsResponseObject(
            invitations=invitations,
            total=total,
            limit=request_object.limit,
            skip=request_object.skip,
        )

    def _get_role_ids(self):
        if self.request_object.roleType == self.request_object.RoleType.MANAGER:
            submitter = self.request_object.submitter
            submitter_role = submitter.get_role()
            is_common_role = submitter_role in RoleName.common_roles()

            if is_common_role:
                org_roles = list(RoleName.common_roles())
            else:
                org_roles = [
                    name
                    for name, role in self._default_roles.organization.items()
                    if role.userType == self.request_object.roleType.value
                ]
            if submitter.organization_id() and submitter.organization.roles:
                org_roles.extend([r.id for r in submitter.organization.roles])
            if submitter_role.id in org_roles:
                if not submitter.deployment_id():
                    return (
                        org_roles
                        if is_common_role
                        else self._exclude_common_roles(org_roles)
                    )
                return (
                    list(RoleName.multi_deployment_roles())
                    if is_common_role
                    else self._exclude_common_roles(RoleName.multi_deployment_roles())
                )

            deployment_roles = list(self._default_roles.deployment_managers.keys())
            deployment = submitter.deployment
            if deployment.roles:
                custom_roles = [r.id for r in deployment.roles]
                deployment_roles.extend(custom_roles)
            if submitter_role.id in deployment_roles:
                return (
                    deployment_roles
                    if is_common_role
                    else self._exclude_common_roles(deployment_roles)
                )
            raise InvalidRoleException
        return [RoleName.USER]

    @staticmethod
    def _exclude_common_roles(roles):
        return list(set(roles) - set(RoleName.common_roles()))

    def _convert_invitations_to_resp_objects(self, invitations: list[Invitation]):
        rsp_invitations = []
        for invitation in invitations:
            data = invitation.to_dict(include_none=False)
            if invitation.role_id in self._default_roles:
                role_name = invitation.role_id
            else:
                if self.request_object.submitter.deployment_id():
                    role = self.request_object.submitter.deployment.find_role_by_id(
                        invitation.role_id
                    )
                else:
                    role = self.request_object.submitter.organization.find_role_by_id(
                        invitation.role_id
                    )
                role_name = role.name if role else None
            data[InvitationResponseModel.ROLE_NAME] = role_name
            rsp_invitations.append(InvitationResponseModel.from_dict(data))
        return rsp_invitations


class RetrieveInvitationsV1UseCase(UseCase):
    @autoparams()
    def __init__(self, repo: InvitationRepository, default_roles: DefaultRoles):
        self._repo = repo
        self._default_roles = default_roles

    def process_request(self, request_object: RetrieveInvitationsRequestObject):
        role_ids = self._get_role_ids()

        invitations, counts = self._repo.retrieve_invitations(
            email=request_object.email,
            skip=request_object.skip,
            limit=request_object.limit,
            role_ids=role_ids,
            deployment_id=request_object.submitter.deployment_id(),
            organization_id=request_object.submitter.organization_id(),
            return_count=True,
            invitation_type=request_object.invitationType,
            sort_fields=request_object.sortFields,
        )

        invitations = self._convert_invitations_to_resp_objects(invitations)

        return RetrieveInvitationsV1ResponseObject(
            invitations=invitations, filtered=counts[0], total=counts[1]
        )

    def _get_role_ids(self):
        if self.request_object.roleType == self.request_object.RoleType.MANAGER:
            submitter = self.request_object.submitter
            submitter_role = submitter.get_role()
            is_common_role = submitter_role.id in RoleName.common_roles()

            if is_common_role:
                org_roles = list(RoleName.common_roles())
            else:
                org_roles = [
                    name
                    for name, role in self._default_roles.organization.items()
                    if role.userType == self.request_object.roleType.value
                ]
            if submitter.organization_id() and submitter.organization.roles:
                org_roles.extend([r.id for r in submitter.organization.roles])
            if submitter_role.id in org_roles:
                if not submitter.deployment_id():
                    return (
                        org_roles
                        if is_common_role
                        else self._exclude_common_roles(org_roles)
                    )
                return (
                    list(RoleName.multi_deployment_roles())
                    if is_common_role
                    else self._exclude_common_roles(RoleName.multi_deployment_roles())
                )

            deployment_roles = list(self._default_roles.deployment_managers.keys())
            deployment = submitter.deployment
            if deployment.roles:
                custom_roles = [r.id for r in deployment.roles]
                deployment_roles.extend(custom_roles)
            if submitter_role.id in deployment_roles:
                return (
                    deployment_roles
                    if is_common_role
                    else self._exclude_common_roles(deployment_roles)
                )
            raise InvalidRoleException
        return [RoleName.USER]

    @staticmethod
    def _exclude_common_roles(roles):
        return list(set(roles) - set(RoleName.common_roles()))

    def _convert_invitations_to_resp_objects(self, invitations: list[Invitation]):
        rsp_invitations = []
        for invitation in invitations:
            data = invitation.to_dict(include_none=False)
            if invitation.role_id in self._default_roles:
                role_name = invitation.role_id
            else:
                if self.request_object.submitter.deployment_id():
                    role = self.request_object.submitter.deployment.find_role_by_id(
                        invitation.role_id
                    )
                else:
                    role = self.request_object.submitter.organization.find_role_by_id(
                        invitation.role_id
                    )
                role_name = role.name if role else None
            data[InvitationResponseModel.ROLE_NAME] = role_name
            if invitation.is_universal:
                data[
                    InvitationResponseModel.INVITATION_LINK
                ] = self._generate_invitation_link(invitation.code)
            if invitation.senderId:
                user = AuthorizationService().retrieve_user_profile(invitation.senderId)
                data[InvitationResponseModel.INVITED_BY] = user.get_full_name()
            rsp_invitations.append(InvitationResponseModel.from_dict(data))

        return rsp_invitations

    @staticmethod
    def _generate_invitation_link(invitation_code: str) -> str:
        link_use_case = GetInvitationLinkUseCase()
        return link_use_case._build_link(invitation_code, False)
