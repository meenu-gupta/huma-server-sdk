import datetime
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.callbacks import register_user_with_role
from extensions.authorization.events import (
    GetDeploymentCustomRoleEvent,
    GetOrganizationCustomRoleEvent,
)
from extensions.authorization.exceptions import CantResendInvitation
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, PermissionType, RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.admin_invitation_request_objects import (
    SendAdminInvitationsRequestObject,
)
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    SendInvitationRequestObject,
    RetrieveInvitationsRequestObject,
    ResendInvitationsRequestObject,
    InvitationValidityRequestObject,
    ResendInvitationsListRequestObject,
    DeleteInvitationsListRequestObject,
)
from extensions.authorization.use_cases.admin_invitation_use_cases import (
    SendAdminInvitationsUseCase,
)
from extensions.authorization.use_cases.invitation_use_cases import (
    SendInvitationsUseCase,
    INVITATION_TOKEN,
    SendInvitationUseCase,
    RetrieveInvitationsUseCase,
    ResendInvitationsUseCase,
    ResendInvitationsListUseCase,
    DeleteInvitationsListUseCase,
)
from extensions.authorization.use_cases.invitation_validity_check_use_case import (
    InvitationValidityUseCase,
)
from extensions.deployment.callbacks import (
    deployment_custom_role_callback,
    organization_custom_role_callback,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.exceptions import UserDoesNotExist
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import get_user
from sdk.auth.events.post_sign_up_event import PostSignUpEvent
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import SignUpRequestObject
from sdk.auth.use_case.auth_use_cases import SignUpUseCase, get_client
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    InvalidRoleException,
    InvalidRequestException,
    InvalidClientIdException,
    InvalidProjectIdException,
)
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import Project, Client, PhoenixServerConfig
from sdk.tests.auth.test_helpers import USER_ID, USER_EMAIL

PROJECT_ID = "test1"
CLIENT_ID = "test1"

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
DEPLOYMENT_ID_2 = "5d386cc6ff885918d96edb24"
ORGANIZATION_ID = "5d386cc6ff885918d96edb4c"
PATIENT_ID = "615f60b3d61eee4a2623cf94"
CUSTOM_DEPLOYMENT_ROLE_ID = "5d386cc6ff885918d96edb2d"
CUSTOM_ORG_ROLE_ID = "0d386cc6ff885918d96edb2d"
INVALID_CUSTOM_ROLE_ID = "5d386cc6ff885918d96edb2a"
CUSTOM_ROLE_NAME = "Test Role"
CUSTOM_ORG_ROLE_NAME = "Test Role Org"
EMAILS = ["test1@huma.com", "test2@huma.com"]
INVALID_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2f"
INVALID_ROLE_ID = "5d386cc6ff885918d96edb2e"
TEST_INVITATION_CODE = "123"
TEST_SHORTENED_INVITATION_CODE = "3lLFJ_d18m3MxMK6"
USER_CLIENT_ID = "c2"
INVITATION_TEST_CASE_PATH = "extensions.authorization.use_cases.invitation_use_cases"
ADMIN = RoleName.ADMIN
TEST_EXPIRES_AT = datetime.datetime(2030, 1, 1)
SAMPLE_ID = "615f60b3d61eee4a2623cf94"
ADMIN_INVITATION_USE_CASE_PATH = "extensions.authorization.use_cases.admin_invitation_use_cases.SendAdminInvitationsUseCase"
ADMIN_INVITATION_REQ_OBJ_PATH = (
    "extensions.authorization.router.admin_invitation_request_objects"
)
INVITATION_OBJECT_ID = "615f60b3d61eee4a2623cf95"


def mocked_g():
    gl = MagicMock()
    role = RoleAssignment.create_role(RoleName.CONTRIBUTOR, DEPLOYMENT_ID)
    gl.user = User(id=USER_ID, roles=[role])
    role = RoleAssignment.create_role(RoleName.SUPER_ADMIN, DEPLOYMENT_ID)
    user = User(id=USER_ID, roles=[role])
    gl.authz_user = AuthorizedUser(user)
    return gl


def get_invitation_sign_up_data(email: str, name: str, invitation_code: str):
    data = get_user(email, name, {"invitationCode": invitation_code})
    data[SignUpRequestObject.PROJECT_ID] = PROJECT_ID
    data[SignUpRequestObject.CLIENT_ID] = CLIENT_ID
    return data


def get_deployment():
    role_data = {
        Role.ID: CUSTOM_DEPLOYMENT_ROLE_ID,
        Role.NAME: CUSTOM_ROLE_NAME,
        Role.PERMISSIONS: [PermissionType.MANAGE_PATIENT_DATA.value],
    }
    role = Role.from_dict(role_data)
    return Deployment(
        id=DEPLOYMENT_ID,
        name="test",
        roles=[role],
        privacyPolicyUrl="privacy_url_val",
        eulaUrl="eula_url_val",
        termAndConditionUrl="term_val",
        onboardingConfigs=[],
    )


def get_organization():
    role_data = {
        Role.ID: CUSTOM_ORG_ROLE_ID,
        Role.NAME: CUSTOM_ORG_ROLE_NAME,
        Role.PERMISSIONS: [PermissionType.MANAGE_PATIENT_DATA.value],
    }
    return Organization(
        name="test",
        privacyPolicyUrl="privacy_url_val_organization",
        eulaUrl="eula_url_val_organization",
        termAndConditionUrl="term_val_organization",
        roles=[Role.from_dict(role_data)],
    )


def get_test_user(role_id: Optional[str], deployment_id: str):
    roles = []
    if role_id:
        roles.append(RoleAssignment.create_role(role_id, deployment_id))

    return User(id="611dfe2b5f627d7d824c297a", email=USER_EMAIL, roles=roles)


class MockDepService:
    def retrieve_deployment(self, deployment_id):
        return get_deployment()


class SendInvitationUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mocked_deployment_repo = MagicMock()
        self.mocked_deployment_repo.retrieve_deployment.return_value = get_deployment()
        self.mocked_organization_repo = MagicMock()
        self.mocked_organization_repo.retrieve_organization.return_value = (
            get_organization()
        )
        self.mocked_invitation_repo = MagicMock()
        self.mocked_invitation_repo.retrieve_proxy_invitation.return_value = None
        self.mocked_auth_repo = MagicMock()
        self.mocked_invitation_adapter = MagicMock()
        self.mocked_token_adapter = MagicMock()
        self.mocked_token = "token"
        self.mocked_token_adapter.create_token.return_value = self.mocked_token
        self.config = MagicMock()
        self.user_client = Client(
            clientId=USER_CLIENT_ID, clientType=Client.ClientType.USER_IOS
        )
        self.manager_client = Client(
            clientId=CLIENT_ID, clientType=Client.ClientType.MANAGER_WEB
        )
        self.config.server.project = Project(
            id=PROJECT_ID,
            clients=[self.manager_client, self.user_client],
        )
        self.config.server.invitation.invitationExpiresAfterMinutes = 10
        self.config.server.invitation.maxInvitationResendTimes = 5
        self.config.server.invitation.shortenedCodeLength = 16

        event_bus = EventBusAdapter()
        event_bus.subscribe(
            GetDeploymentCustomRoleEvent, deployment_custom_role_callback
        )

        def configure_with_binder(binder: inject.Binder):
            binder.bind(PhoenixServerConfig, self.config)
            binder.bind(AuthorizationRepository, self.mocked_auth_repo)
            binder.bind(EventBusAdapter, event_bus)
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(DeploymentRepository, self.mocked_deployment_repo)
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(OrganizationRepository, self.mocked_organization_repo)

        inject.clear_and_configure(config=configure_with_binder)

    def get_invitation_use_case(self):
        use_case = SendInvitationsUseCase(**self._common_invitation_use_case_kwargs())
        use_case.request_object = SendInvitationsRequestObject()
        return use_case

    def _common_invitation_use_case_kwargs(self):
        return {
            "invitation_repo": self.mocked_invitation_repo,
            "invitation_adapter": self.mocked_invitation_adapter,
            "token_adapter": self.mocked_token_adapter,
            "server_config": self.config,
            "deployment_repo": self.mocked_deployment_repo,
            "auth_repo": self.mocked_auth_repo,
            "organization_repo": self.mocked_organization_repo,
        }

    def test_send_invitation_use_case(self):
        invitation = Invitation(
            email=USER_EMAIL,
            code=self.mocked_token,
            roles=[RoleAssignment.create_role(RoleName.USER, DEPLOYMENT_ID)],
            clientId=CLIENT_ID,
        )
        data = {
            SendInvitationRequestObject.INVITATION: invitation,
            SendInvitationRequestObject.SENDER: mocked_g().authz_user,
            SendInvitationRequestObject.CLIENT: self.manager_client,
        }
        request_object = SendInvitationRequestObject.from_dict(data)
        use_case = SendInvitationUseCase(**self._common_invitation_use_case_kwargs())
        use_case.execute(request_object)
        self.mocked_invitation_adapter.send_user_invitation_email.assert_called_once_with(
            USER_EMAIL, self.user_client, request_object.language, self.mocked_token
        )

    def test_send_invitation_default_role(self):
        self.mocked_auth_repo.retrieve_simple_user_profile.side_effect = (
            UserDoesNotExist()
        )
        self.mocked_organization_repo.retrieve_organization_ids.return_value = [
            ORGANIZATION_ID
        ]
        test_roles = [
            RoleName.DEPLOYMENT_STAFF,
            RoleName.ADMIN,
            RoleName.CONTRIBUTOR,
            RoleName.CALL_CENTER,
            RoleName.EXPORTER,
            RoleName.MANAGER,
            RoleName.IDENTIFIABLE_EXPORT,
        ]
        use_case = self.get_invitation_use_case()
        for role in test_roles:
            request_data = {
                SendInvitationsRequestObject.EMAILS: EMAILS,
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
                SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
                SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
            }
            if role in RoleName.org_roles():
                request_data.update(
                    {SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID}
                )
            elif role in RoleName.multi_deployment_roles():
                ids = [DEPLOYMENT_ID, DEPLOYMENT_ID_2]
                request_data.update(
                    {
                        SendInvitationsRequestObject.DEPLOYMENT_IDS: ids,
                        SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                    }
                )
            elif role == RoleName.PROXY:
                request_data.update(
                    {SendInvitationsRequestObject.PATIENT_ID: PATIENT_ID}
                )
            else:
                request_data.update(
                    {SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID]}
                )

            request_object = SendInvitationsRequestObject.from_dict(request_data)
            result = use_case.execute(request_object)
            self.assertTrue(result.value.ok)
            calls = self.mocked_invitation_adapter.send_invitation_email.call_count
            self.assertEqual(len(EMAILS), calls)
            self.mocked_invitation_adapter.send_invitation_email.reset_mock()

    def test_send_invitation_user_role(self):
        self.mocked_auth_repo.retrieve_simple_user_profile.side_effect = (
            UserDoesNotExist()
        )
        use_case = self.get_invitation_use_case()

        request_data = {
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }

        request_object = SendInvitationsRequestObject.from_dict(request_data)
        result = use_case.execute(request_object)
        self.assertTrue(result.value.ok)
        calls = self.mocked_invitation_adapter.send_user_invitation_email.call_count
        self.assertEqual(len(EMAILS), calls)

    @patch(
        "extensions.deployment.service.deployment_service.DeploymentService",
        MockDepService,
    )
    def test_send_invitation_existing_custom_role(self):
        self.mocked_auth_repo.retrieve_simple_user_profile.side_effect = (
            UserDoesNotExist()
        )
        use_case = self.get_invitation_use_case()

        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.ROLE_ID: CUSTOM_DEPLOYMENT_ROLE_ID,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        result = use_case.execute(request_object)
        self.assertTrue(result.value.ok)
        calls = self.mocked_invitation_adapter.send_invitation_email.call_count
        self.assertEqual(calls, len(EMAILS))

    def test_send_invitation_not_existing_custom_role_failure(self):
        self.mocked_auth_repo.retrieve_simple_user_profile.side_effect = (
            UserDoesNotExist()
        )
        use_case = self.get_invitation_use_case()

        # testing with invalid deployment id
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [INVALID_DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.ROLE_ID: INVALID_CUSTOM_ROLE_ID,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        with self.assertRaises(InvalidRoleException):
            use_case.execute(request_object)

        # invalid role id
        request_data[SendInvitationsRequestObject.DEPLOYMENT_IDS] = [DEPLOYMENT_ID]
        request_data[SendInvitationsRequestObject.ROLE_ID] = INVALID_ROLE_ID
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        self.assertRaises(InvalidRoleException, use_case.execute, request_object)

    def test_send_invitation_superadmin_role_failure(self):
        self.mocked_auth_repo.retrieve_simple_user_profile.side_effect = (
            UserDoesNotExist()
        )
        use_case = self.get_invitation_use_case()
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.ROLE_ID: RoleName.SUPER_ADMIN,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        self.assertRaises(InvalidRoleException, use_case.execute, request_object)

    def test_send_invitation_code_user_claim(self):
        def lookup_user(*args, **kwargs):
            if user_id := kwargs.get("user_id"):
                if user_id == PATIENT_ID:
                    user_role = RoleAssignment.create_role(
                        RoleName.CONTRIBUTOR, DEPLOYMENT_ID
                    )
                    return User(id=PATIENT_ID, roles=[user_role])
            raise UserDoesNotExist

        self.mocked_auth_repo.retrieve_simple_user_profile = lookup_user
        use_case = self.get_invitation_use_case()
        roles = list(DefaultRoles().deployment)
        roles.remove(RoleName.SUPER_ADMIN)
        roles.remove(RoleName.HUMA_SUPPORT)
        roles.remove(RoleName.ACCOUNT_MANAGER)
        for role in RoleName.common_roles():
            roles.remove(role)
        for role in roles:
            request_data = {
                SendInvitationsRequestObject.EMAILS: EMAILS,
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
                SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
                SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
            }
            if role == RoleName.PROXY:
                request_data[SendInvitationsRequestObject.PATIENT_ID] = PATIENT_ID
            else:
                request_data[SendInvitationsRequestObject.DEPLOYMENT_IDS] = [
                    DEPLOYMENT_ID
                ]

            request_object = SendInvitationsRequestObject.from_dict(request_data)
            result = use_case.execute(request_object)
            self.assertTrue(result.value.ok)
            args = self.mocked_token_adapter.create_token.call_args.kwargs
            self.assertEqual(args["user_claims"]["privacyPolicyUrl"], "privacy_url_val")
            self.assertEqual(args["user_claims"]["eulaUrl"], "eula_url_val")
            self.assertEqual(args["user_claims"]["termAndConditionUrl"], "term_val")
            self.mocked_invitation_adapter.send_invitation_email.reset_mock()

    def test_send_invitation_superadmin_email_failure(self):
        user = get_test_user(RoleName.SUPER_ADMIN, "*")
        self.mocked_auth_repo.retrieve_simple_user_profile.return_value = user
        use_case = self.get_invitation_use_case()
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [USER_EMAIL],
            SendInvitationsRequestObject.ROLE_ID: RoleName.CONTRIBUTOR,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        response = use_case.execute(request_object)
        has_signed_response = hasattr(response.value, "alreadySignedUpEmails")
        self.assertTrue(has_signed_response)
        self.assertEqual([USER_EMAIL], response.value.alreadySignedUpEmails)

    def test_get_role(self):
        use_case = self.get_invitation_use_case()
        use_case.request_object = SendInvitationsRequestObject(
            roleId=CUSTOM_DEPLOYMENT_ROLE_ID,
            deploymentIds=[DEPLOYMENT_ID],
        )
        self.assertEqual(CUSTOM_ROLE_NAME, use_case.get_role().name)

    def test_send_invitation_update_user_no_roles(self):
        user = get_test_user(None, "someOtherDeploymentId")
        self.mocked_auth_repo.retrieve_simple_user_profile.return_value = user
        use_case = self.get_invitation_use_case()
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [user.email],
            SendInvitationsRequestObject.ROLE_ID: RoleName.CONTRIBUTOR,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        result = use_case.execute(request_object)
        self.mocked_auth_repo.retrieve_simple_user_profile.assert_called_with(
            user_id=user.id
        )
        self.assertTrue(result.value.ok)
        self.assertIsNone(result.value.alreadySignedUpEmails)

    def test_failure_invite_user_with_existing_role(self):
        user = get_test_user(RoleName.DEPLOYMENT_STAFF, "someOtherDeploymentId")
        self.mocked_auth_repo.retrieve_simple_user_profile.return_value = user
        use_case = self.get_invitation_use_case()
        request_data = {
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [user.email],
            SendInvitationsRequestObject.ROLE_ID: RoleName.DEPLOYMENT_STAFF,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        result = use_case.execute(request_object)

        self.assertTrue(result.value.ok)
        self.assertEqual(1, len(result.value.alreadySignedUpEmails))

    def test_request_object(self):
        use_cases = (
            (
                ADMIN,
                [DEPLOYMENT_ID, DEPLOYMENT_ID],
                InvalidRequestException,
            ),
            (
                RoleName.CONTRIBUTOR,
                [DEPLOYMENT_ID, DEPLOYMENT_ID],
                InvalidRequestException,
            ),
            (
                RoleName.USER,
                [DEPLOYMENT_ID, DEPLOYMENT_ID],
                InvalidRequestException,
            ),
            (
                RoleName.ORGANIZATION_STAFF,
                [DEPLOYMENT_ID],
                ConvertibleClassValidationError,
            ),
            (
                RoleName.ACCESS_CONTROLLER,
                [DEPLOYMENT_ID],
                ConvertibleClassValidationError,
            ),
        )
        request_data = {
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        for role, deployments, error in use_cases:
            data = {
                **request_data,
                SendInvitationsRequestObject.DEPLOYMENT_IDS: deployments,
                SendInvitationsRequestObject.ROLE_ID: role,
            }
            with self.assertRaises(error):
                SendInvitationsRequestObject.from_dict(data)

    def test_failure_request_organization_for_contributor_staff(self):
        request_data = {
            SendInvitationsRequestObject.ORGANIZATION_ID: DEPLOYMENT_ID,
            SendInvitationsRequestObject.EMAILS: EMAILS,
            SendInvitationsRequestObject.ROLE_ID: RoleName.CONTRIBUTOR,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SendInvitationsRequestObject.from_dict(request_data)

    def test_get_policy_data_based_on_role_one_deployment_call_center_and_deployment_staff_roles(
        self,
    ):
        roles = DefaultRoles()
        accepted_roles = [roles.deployment_staff, roles.call_center]
        use_case = self.get_invitation_use_case()
        for role in accepted_roles:
            res = use_case._get_policy_data_based_on_role(
                role, [DEPLOYMENT_ID], ORGANIZATION_ID, PATIENT_ID
            )
            deployment = get_deployment()
            self.assertEqual(
                res[Deployment.PRIVACY_POLICY_URL], deployment.privacyPolicyUrl
            )
            self.assertEqual(res[Deployment.EULA_URL], deployment.eulaUrl)
            self.assertEqual(
                res[Deployment.TERM_AND_CONDITION_URL], deployment.termAndConditionUrl
            )

    def test_get_policy_data_based_on_role_multiple_deployments(self):
        roles = DefaultRoles()
        accepted_roles = [
            roles.deployment_staff,
            roles.call_center,
            roles.access_controller,
            roles.organization_staff,
        ]
        use_case = self.get_invitation_use_case()
        self.mocked_organization_repo.retrieve_organization_ids.return_value = [
            ORGANIZATION_ID
        ]
        for role in accepted_roles:
            res = use_case._get_policy_data_based_on_role(
                role, [DEPLOYMENT_ID, DEPLOYMENT_ID_2], ORGANIZATION_ID, PATIENT_ID
            )
            organization = get_organization()
            self.assertEqual(
                res[Organization.PRIVACY_POLICY_URL], organization.privacyPolicyUrl
            )
            self.assertEqual(res[Organization.EULA_URL], organization.eulaUrl)
            self.assertEqual(
                res[Organization.TERM_AND_CONDITION_URL],
                organization.termAndConditionUrl,
            )

    def test_get_policy_data_based_on_role_any_other_role_one_deployment(self):
        roles = DefaultRoles()
        accepted_roles = [roles.user, roles.proxy]
        use_case = self.get_invitation_use_case()
        for role in accepted_roles:
            res = use_case._get_policy_data_based_on_role(
                role, [DEPLOYMENT_ID], ORGANIZATION_ID, PATIENT_ID
            )
            deployment = get_deployment()
            self.assertEqual(
                res[Deployment.PRIVACY_POLICY_URL], deployment.privacyPolicyUrl
            )
            self.assertEqual(res[Deployment.EULA_URL], deployment.eulaUrl)
            self.assertEqual(
                res[Deployment.TERM_AND_CONDITION_URL], deployment.termAndConditionUrl
            )

    def test_get_policy_data_based_on_role_any_other_role_multiple_deployment(self):
        roles = DefaultRoles()
        accepted_roles = [roles.user, roles.proxy]
        use_case = self.get_invitation_use_case()
        for role in accepted_roles:
            res = use_case._get_policy_data_based_on_role(
                role, [DEPLOYMENT_ID, DEPLOYMENT_ID_2], ORGANIZATION_ID, PATIENT_ID
            )
            deployment = get_deployment()
            self.assertEqual(
                res[Deployment.PRIVACY_POLICY_URL], deployment.privacyPolicyUrl
            )
            self.assertEqual(res[Deployment.EULA_URL], deployment.eulaUrl)
            self.assertEqual(
                res[Deployment.TERM_AND_CONDITION_URL], deployment.termAndConditionUrl
            )

    def test_send_invitation_uses_first_available_user_client(self):
        mocked_auth_repo = MagicMock()
        mocked_auth_repo.retrieve_simple_user_profile.side_effect = [UserDoesNotExist]
        use_case = SendInvitationsUseCase(
            self.mocked_invitation_repo,
            self.mocked_invitation_adapter,
            self.mocked_token_adapter,
            self.config,
            self.mocked_deployment_repo,
            mocked_auth_repo,
            self.mocked_organization_repo,
        )

        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [USER_EMAIL],
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        request_object = SendInvitationsRequestObject.from_dict(request_data)
        use_case.execute(request_object)
        self.mocked_invitation_adapter.send_user_invitation_email.assert_called_once_with(
            USER_EMAIL, self.user_client, request_object.language, self.mocked_token
        )

    def test_failure_with_invalid_client_id(self):
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [USER_EMAIL],
            SendInvitationsRequestObject.ROLE_ID: RoleName.CONTRIBUTOR,
            SendInvitationsRequestObject.CLIENT_ID: "invalid client id",
            SendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        with self.assertRaises(InvalidClientIdException):
            SendInvitationsRequestObject.from_dict(request_data)

    def test_failure_with_invalid_project_id(self):
        request_data = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.EMAILS: [USER_EMAIL],
            SendInvitationsRequestObject.ROLE_ID: RoleName.CONTRIBUTOR,
            SendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendInvitationsRequestObject.PROJECT_ID: "invalid project id",
            SendInvitationsRequestObject.SUBMITTER: mocked_g().authz_user,
        }
        with self.assertRaises(InvalidProjectIdException):
            SendInvitationsRequestObject.from_dict(request_data)


class SignUpViaInvitationUseCase(unittest.TestCase):
    config: PhoenixServerConfig = None
    event_bus: EventBusAdapter = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_auth_repo = MagicMock()
        cls.mocked_token_adapter = MagicMock()
        cls.config = MagicMock()
        user_types = [
            Role.UserType.SUPER_ADMIN,
            Role.UserType.MANAGER,
            Role.UserType.USER,
            Role.UserType.PROXY,
            Role.UserType.SERVICE_ACCOUNT,
        ]
        cls.config.server.project = Project(
            id=PROJECT_ID, clients=[Client(clientId=CLIENT_ID, roleIds=user_types)]
        )
        cls.config.server.invitation.invitationExpiresAfterMinutes = 10
        cls.config.server.auth.signedUrlSecret = "secret"

        mocked_deployment_repo = MagicMock()
        mocked_deployment_repo.retrieve_deployment.return_value = get_deployment()
        mocked_auth_repo = MagicMock()
        mocked_auth_repo.create_user.return_value = USER_ID
        mocked_org_repo = MagicMock()
        mocked_org_repo.retrieve_organization.return_value = get_organization()

        def configure_with_binder(binder: inject.Binder):
            binder.bind(PhoenixServerConfig, cls.config)
            binder.bind(AuthRepository, mocked_auth_repo)
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(DeploymentRepository, mocked_deployment_repo)
            binder.bind(EventBusAdapter, EventBusAdapter())
            binder.bind(OrganizationRepository, mocked_org_repo)
            binder.bind(AuthorizationRepository, MagicMock())
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())
            binder.bind(InvitationRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)
        event_bus = inject.instance(EventBusAdapter)
        event_bus.subscribe(PostSignUpEvent, register_user_with_role)
        event_bus.subscribe(
            GetDeploymentCustomRoleEvent, deployment_custom_role_callback
        )
        event_bus.subscribe(
            GetOrganizationCustomRoleEvent, organization_custom_role_callback
        )

    def get_sign_up_use_case(self):
        return SignUpUseCase(
            server_config=self.config,
            confirmation_adapter=MagicMock(),
        )

    def create_invitation(
        self, email: str, role_id: str, deployment_id: str, org_id=None
    ):
        adapter = JwtTokenAdapter(JwtTokenConfig(secret="test"), self.config)
        token = adapter.create_token(email, INVITATION_TOKEN)
        if role_id in RoleName.org_roles():
            resource_id = org_id
        else:
            resource_id = deployment_id
        role = RoleAssignment.create_role(role_id, resource_id)

        return Invitation(
            code=token,
            email=email,
            roles=[role],
        )

    @patch(
        "extensions.deployment.service.deployment_service.DeploymentService",
        MockDepService,
    )
    @patch("extensions.authorization.callbacks.callbacks.AuthorizationService")
    @patch("extensions.authorization.callbacks.callbacks.retrieve_invitation")
    @patch("extensions.authorization.validators.check_role_id_valid_for_organization")
    def test_sign_up_with_invitation_code_custom_role(
        self,
        check_role_valid_org_mock2,
        retrieve_invitation_mock,
        mocked_auth_service,
    ):
        mocked_auth_service().create_user.return_value = USER_ID
        check_role_valid_org_mock2.return_value = False

        invitation = self.create_invitation(
            USER_EMAIL, CUSTOM_DEPLOYMENT_ROLE_ID, DEPLOYMENT_ID
        )
        retrieve_invitation_mock.return_value = invitation

        use_case = self.get_sign_up_use_case()
        request_data = get_invitation_sign_up_data(
            USER_EMAIL, "Tester", TEST_INVITATION_CODE
        )
        request_object = SignUpRequestObject.from_dict(request_data)
        use_case.execute(request_object)
        created_user = mocked_auth_service().create_user.call_args.args[0]
        self.assertEqual(len(created_user.roles), 1)
        role = created_user.roles[0]
        self.assertEqual(role.roleId, CUSTOM_DEPLOYMENT_ROLE_ID)
        self.assertEqual(role.resource, f"deployment/{DEPLOYMENT_ID}")
        deployment = get_deployment()
        self.assertEqual(deployment.roles[0].userType, created_user.roles[0].userType)

    @patch("extensions.authorization.models.user.validators")
    @patch("extensions.authorization.callbacks.callbacks.DeploymentService")
    @patch("extensions.authorization.callbacks.callbacks.retrieve_invitation")
    def test_sign_up_with_invitation_code_invalid(
        self, retrieve_invitation_mock, deployment_service_mock, mock_validators
    ):
        # marking code as invalid
        mock_validators.check_role_id_valid_for_organization.side_effect = (
            ConvertibleClassValidationError()
        )
        with self.assertRaises(ConvertibleClassValidationError):
            invitation = self.create_invitation(
                USER_EMAIL, CUSTOM_DEPLOYMENT_ROLE_ID, DEPLOYMENT_ID
            )

            deployment_service_mock.retrieve_deployment = get_deployment()
            retrieve_invitation_mock.return_value = invitation
            use_case = self.get_sign_up_use_case()
            request_data = get_invitation_sign_up_data(
                USER_EMAIL, "Tester", TEST_INVITATION_CODE
            )

            request_object = SignUpRequestObject.from_dict(request_data)
            use_case.execute(request_object)

    @patch(
        "extensions.authorization.callbacks.callbacks.check_if_participant_off_boarded"
    )
    @patch("extensions.authorization.callbacks.callbacks.AuthorizationService")
    @patch("extensions.deployment.service.deployment_service.DeploymentService")
    @patch("extensions.authorization.callbacks.callbacks.retrieve_invitation")
    def test_sign_up_with_invitation_code_default_roles(
        self,
        retrieve_invitation_mock,
        deployment_service_mock,
        mocked_auth_service,
        mocked_check,
    ):
        mocked_auth_service().create_user.return_value = USER_ID
        deployment_service_mock.retrieve_deployment = get_deployment()
        mocked_check.return_value = False

        roles = DefaultRoles()
        for default_role in roles:
            invitation = self.create_invitation(
                USER_EMAIL, default_role, DEPLOYMENT_ID, ORGANIZATION_ID
            )
            retrieve_invitation_mock.return_value = invitation

            request_data = get_invitation_sign_up_data(
                USER_EMAIL, "Tester", TEST_INVITATION_CODE
            )
            request_object = SignUpRequestObject.from_dict(request_data)

            use_case = self.get_sign_up_use_case()
            use_case.execute(request_object)
            created_user = mocked_auth_service().create_user.call_args.args[0]
            self.assertEqual(len(created_user.roles), 1)
            role = created_user.roles[0]
            self.assertEqual(
                created_user.roles[0].userType, roles[default_role].userType
            )
            self.assertEqual(role.roleId, default_role)
            expected_resource = "deployment"
            expected_resource_id = DEPLOYMENT_ID
            if default_role in RoleName.org_roles():
                expected_resource = "organization"
                expected_resource_id = ORGANIZATION_ID

            super_roles = (
                RoleName.SUPER_ADMIN,
                RoleName.HUMA_SUPPORT,
            )
            if role.roleId in super_roles:
                expected_resource_id = "*"

            expected = f"{expected_resource}/{expected_resource_id}"
            self.assertEqual(expected, role.resource, f"Failed on {default_role} role")


class PendingInvitationsTestCase(unittest.TestCase):
    mocked_organization_repo = None
    mocked_deployment_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_deployment_repo = MagicMock()
        cls.mocked_deployment_repo.retrieve_deployment.return_value = get_deployment()
        cls.mocked_organization_repo = MagicMock()
        cls.mocked_organization_repo.retrieve_organization.return_value = (
            get_organization()
        )

        def configure_with_binder(binder: inject.Binder):
            binder.bind(EventBusAdapter, EventBusAdapter())
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(DeploymentRepository, cls.mocked_deployment_repo)
            binder.bind(OrganizationRepository, cls.mocked_organization_repo)
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())

            config_path = Path(__file__).parent.joinpath("config.test.yaml")
            config = PhoenixServerConfig.get(config_path, {})
            binder.bind(PhoenixServerConfig, config)

        inject.clear_and_configure(config=configure_with_binder)

    @staticmethod
    def _prepare_use_case(
        role_type: RetrieveInvitationsRequestObject.RoleType, submitter: AuthorizedUser
    ):
        use_case = RetrieveInvitationsUseCase()
        data = {
            RetrieveInvitationsRequestObject.ROLE_TYPE: role_type,
            RetrieveInvitationsRequestObject.SUBMITTER: submitter,
            RetrieveInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            RetrieveInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
        }
        request_obj = RetrieveInvitationsRequestObject.from_dict(data)
        use_case.request_object = request_obj
        return use_case

    def _get_role_ids(
        self,
        role_type: RetrieveInvitationsRequestObject.RoleType,
        submitter: AuthorizedUser,
    ):
        return self._prepare_use_case(role_type, submitter)._get_role_ids()

    def _convert_invitations_to_resp_objects(
        self, submitter: AuthorizedUser, invitations: list[Invitation]
    ):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        use_case = self._prepare_use_case(role_type, submitter)
        return use_case._convert_invitations_to_resp_objects(invitations)

    @staticmethod
    def _get_org_submitter(role_id=RoleName.ORGANIZATION_STAFF):
        role = RoleAssignment.create_role(role_id, ORGANIZATION_ID)
        user = User(id=USER_ID, roles=[role])
        return AuthorizedUser(user)

    @staticmethod
    def _get_deployment_submitter(role_id=ADMIN):
        role = RoleAssignment.create_role(role_id, DEPLOYMENT_ID)
        user = User(id=USER_ID, roles=[role])
        return AuthorizedUser(user)

    @staticmethod
    def _get_invitation(role: str, resource_id: str):
        org_role = RoleAssignment.create_role(role, resource_id)
        invitation = Invitation(
            roles=[org_role],
            code=TEST_INVITATION_CODE,
            shortenedCode=TEST_SHORTENED_INVITATION_CODE,
            expiresAt=TEST_EXPIRES_AT,
        )
        return invitation

    def test_get_user_role_ids__org_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.USER
        role_ids = self._get_role_ids(role_type, self._get_org_submitter())
        self.assertEqual([RoleName.USER], role_ids)

    def test_get_user_role_ids__deployment_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.USER
        role_ids = self._get_role_ids(role_type, self._get_deployment_submitter())
        self.assertEqual([RoleName.USER], role_ids)

    def test_get_manager_role_ids__deployment_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        role_ids = self._get_role_ids(role_type, self._get_deployment_submitter())
        expected_role_ids = [
            ADMIN,
            RoleName.CONTRIBUTOR,
            RoleName.MANAGER,
            CUSTOM_DEPLOYMENT_ROLE_ID,
        ]
        self.assertEqual(expected_role_ids.sort(), role_ids.sort())

    def test_get_manager_role_ids_administartor_deployment_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        role_ids = self._get_role_ids(
            role_type, self._get_deployment_submitter(RoleName.ADMINISTRATOR)
        )
        expected_role_ids = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        self.assertEqual(expected_role_ids.sort(), role_ids.sort())

    def test_get_manager_role_ids__general_org_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        role_ids = self._get_role_ids(role_type, self._get_org_submitter())
        expected_role_ids = [
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
            CUSTOM_ORG_ROLE_ID,
        ]
        self.assertEqual(expected_role_ids.sort(), role_ids.sort())

    def test_get_manager_role_ids__deployment_staff_org_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        submitter = self._get_org_submitter(RoleName.DEPLOYMENT_STAFF)
        role_ids = self._get_role_ids(role_type, submitter)
        expected_role_ids = [
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
        ]
        self.assertEqual(expected_role_ids.sort(), role_ids.sort())

    def test_get_manager_role_ids_administrator_org_view(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER
        submitter = self._get_org_submitter(RoleName.ADMINISTRATOR)
        role_ids = self._get_role_ids(role_type, submitter)
        expected_role_ids = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        self.assertEqual(expected_role_ids.sort(), role_ids.sort())

    def test_convert_organization_invitation(self):
        submitter = self._get_org_submitter(RoleName.ACCESS_CONTROLLER)
        invitation = self._get_invitation(RoleName.ORGANIZATION_STAFF, ORGANIZATION_ID)
        rsp_data = self._convert_invitations_to_resp_objects(submitter, [invitation])
        self.assertEqual(1, len(rsp_data))
        self.assertEqual(RoleName.ORGANIZATION_STAFF, rsp_data[0].roleName)

    def test_convert_custom_organization_invitation(self):
        event_bus = inject.instance(EventBusAdapter)
        event_bus.subscribe(
            GetOrganizationCustomRoleEvent, organization_custom_role_callback
        )
        submitter = self._get_org_submitter(RoleName.ACCESS_CONTROLLER)
        invitation = self._get_invitation(CUSTOM_ORG_ROLE_ID, ORGANIZATION_ID)
        rsp_data = self._convert_invitations_to_resp_objects(submitter, [invitation])
        self.assertEqual(1, len(rsp_data))
        self.assertEqual(CUSTOM_ORG_ROLE_NAME, rsp_data[0].roleName)

    def test_convert_custom_deployment_invitation(self):
        event_bus = inject.instance(EventBusAdapter)
        event_bus.subscribe(
            GetDeploymentCustomRoleEvent, deployment_custom_role_callback
        )
        submitter = self._get_deployment_submitter(ADMIN)
        invitation = self._get_invitation(CUSTOM_DEPLOYMENT_ROLE_ID, DEPLOYMENT_ID)
        rsp_data = self._convert_invitations_to_resp_objects(submitter, [invitation])
        self.assertEqual(1, len(rsp_data))
        self.assertEqual(CUSTOM_ROLE_NAME, rsp_data[0].roleName)

    def test_convert_deployment_invitation(self):
        submitter = self._get_deployment_submitter(ADMIN)
        invitation = self._get_invitation(ADMIN, DEPLOYMENT_ID)
        rsp_data = self._convert_invitations_to_resp_objects(submitter, [invitation])
        self.assertEqual(1, len(rsp_data))
        self.assertEqual(ADMIN, rsp_data[0].roleName)


class MockAuthUser:
    instance = MagicMock()


class ResendInvitationsTestCase(unittest.TestCase):
    _invitation_repo = None
    _server_config = None
    _req_obj_data = {}
    _auth_repo = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._invitation_repo = MagicMock()
        invitation = Invitation(
            email=USER_EMAIL,
            code="code",
            roles=[],
            clientId=CLIENT_ID,
            numberOfTry=4,
            senderId=SAMPLE_ID,
        )
        cls._invitation_repo.retrieve_invitation.return_value = invitation
        cls._invitation_repo.retrieve_invitation_list_by_code_list.return_value = [
            invitation
        ]

        cls._server_config = MagicMock()
        cls._server_config.server.invitation.maxInvitationResendTimes = 3
        user_client = Client(clientId=CLIENT_ID, clientType=Client.ClientType.USER_IOS)
        cls._server_config.server.project = Project(
            id=PROJECT_ID,
            clients=[
                user_client,
            ],
        )
        cls._req_obj_data = {
            ResendInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            ResendInvitationsRequestObject.EMAIL: USER_EMAIL,
            ResendInvitationsRequestObject.INVITATION_CODE: "invitation_code",
            ResendInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
        }
        cls._req_list_obj_data = {
            ResendInvitationsListRequestObject.CLIENT_ID: CLIENT_ID,
            ResendInvitationsListRequestObject.INVITATIONS_LIST: [
                {
                    ResendInvitationsListRequestObject.InvitationItem.EMAIL: USER_EMAIL,
                    ResendInvitationsListRequestObject.InvitationItem.INVITATION_CODE: "invitation_code",
                }
            ],
            ResendInvitationsListRequestObject.PROJECT_ID: PROJECT_ID,
        }
        cls._auth_repo = MagicMock()
        cls._auth_repo.retrieve_user.return_value = User.from_dict({User.ID: SAMPLE_ID})

        def configure_with_binder(binder: inject.Binder):
            binder.bind(InvitationRepository, cls._invitation_repo)
            binder.bind(EmailInvitationAdapter, MagicMock())
            binder.bind(TokenAdapter, MagicMock())
            binder.bind(PhoenixServerConfig, cls._server_config)
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(AuthorizationRepository, cls._auth_repo)
            binder.bind(OrganizationRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    def test_failure_resend_deployment_invitation(self):
        req = ResendInvitationsRequestObject.from_dict(
            {**self._req_obj_data, ResendInvitationsRequestObject.EMAIL: EMAILS[0]}
        )
        with self.assertRaises(InvalidRequestException):
            ResendInvitationsUseCase().execute(req)

    def test_failure_quantity_limitation(self):
        self._server_config.server.invitation.maxInvitationResendTimes = 3
        req = ResendInvitationsRequestObject.from_dict(self._req_obj_data)
        with self.assertRaises(CantResendInvitation):
            ResendInvitationsUseCase().execute(req)

    @patch(
        f"{INVITATION_TEST_CASE_PATH}.ResendInvitationsUseCase._get_initial_submitter"
    )
    @patch(f"{INVITATION_TEST_CASE_PATH}.SendInvitationRequestObject")
    @patch(f"{INVITATION_TEST_CASE_PATH}.SendInvitationUseCase")
    def test_success_resend_invitation(
        self, mock_use_case, mock_request_obj, mock_submitter_func
    ):
        self._server_config.server.invitation.maxInvitationResendTimes = 5
        req = ResendInvitationsRequestObject.from_dict(self._req_obj_data)
        mock_submitter_func.return_value = MagicMock(spec_set=AuthorizedUser)
        ResendInvitationsUseCase().execute(req)
        mock_request_obj.from_dict.assert_called_once_with(
            {
                mock_request_obj.INVITATION: self._invitation_repo.retrieve_invitation(),
                mock_request_obj.SENDER: mock_submitter_func(),
                mock_request_obj.CLIENT: get_client(
                    self._server_config.server.project,
                    self._invitation_repo.retrieve_invitation().clientId,
                ),
                mock_request_obj.LANGUAGE: req.language,
            }
        )

        mock_use_case().execute.assert_called_with(mock_request_obj.from_dict())
        self._invitation_repo.update_invitation.assert_called_with(
            self._invitation_repo.retrieve_invitation()
        )

    def test_failure_with_invalid_client_id(self):
        with self.assertRaises(InvalidClientIdException):
            ResendInvitationsRequestObject.from_dict(
                {
                    **self._req_obj_data,
                    ResendInvitationsRequestObject.CLIENT_ID: "invalid client id",
                }
            )

    def test_failure_with_invalid_project_id(self):
        with self.assertRaises(InvalidProjectIdException):
            ResendInvitationsRequestObject.from_dict(
                {
                    **self._req_obj_data,
                    ResendInvitationsRequestObject.PROJECT_ID: "invalid project id",
                }
            )

    @patch(
        f"{INVITATION_TEST_CASE_PATH}.ResendInvitationsUseCase._get_initial_submitter"
    )
    @patch(f"{INVITATION_TEST_CASE_PATH}.SendInvitationRequestObject")
    @patch(f"{INVITATION_TEST_CASE_PATH}.SendInvitationUseCase")
    def test_success_resend_invitations_list(
        self,
        mock_use_case,
        mock_request_obj,
        mock_submitter_func,
    ):
        self._server_config.server.invitation.maxInvitationResendTimes = 5
        req = ResendInvitationsListRequestObject.from_dict(self._req_list_obj_data)
        mock_submitter_func.return_value = MagicMock(spec_set=AuthorizedUser)
        ResendInvitationsListUseCase().execute(req)
        mock_request_obj.from_dict.assert_called_once_with(
            {
                mock_request_obj.INVITATION: self._invitation_repo.retrieve_invitation_list_by_code_list()[
                    0
                ],
                mock_request_obj.SENDER: mock_submitter_func(),
                mock_request_obj.CLIENT: get_client(
                    self._server_config.server.project,
                    self._invitation_repo.retrieve_invitation().clientId,
                ),
                mock_request_obj.LANGUAGE: req.language,
            }
        )

        mock_use_case().execute.assert_called_with(mock_request_obj.from_dict())
        self._invitation_repo.update_invitation.assert_called_with(
            self._invitation_repo.retrieve_invitation()
        )


class DeleteInvitationsListTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._invitation_repo = MagicMock()
        cls._req_delete_list_obj_data = {
            DeleteInvitationsListRequestObject.INVITATION_ID_LIST: [
                INVITATION_OBJECT_ID
            ],
            DeleteInvitationsListRequestObject.INVITATION_TYPE: InvitationType.PERSONAL.value,
        }

        def configure_with_binder(binder: inject.Binder):
            binder.bind(InvitationRepository, cls._invitation_repo)

        inject.clear_and_configure(config=configure_with_binder)

    def test_delete_invitation_list(self):
        req_obj = DeleteInvitationsListRequestObject.from_dict(
            self._req_delete_list_obj_data
        )
        self._invitation_repo.delete_invitation_list.return_value = 1
        rsp = DeleteInvitationsListUseCase().execute(req_obj)
        self._invitation_repo.delete_invitation_list.assert_called_with(
            invitation_id_list=req_obj.invitationIdList,
            invitation_type=req_obj.invitationType,
        )
        self.assertEqual(1, rsp.value.deletedInvitations)


class SendAdminInvitationsUseCaseTestCase(unittest.TestCase):
    def setUp(self):
        self.org_repo = MagicMock()
        self._server_config = MagicMock()
        user_client = Client(clientId=CLIENT_ID, clientType=Client.ClientType.USER_IOS)
        self._server_config.server.project = Project(
            id=PROJECT_ID,
            clients=[
                user_client,
            ],
        )

        def configure_with_binder(binder: inject.Binder):
            binder.bind(InvitationRepository, MagicMock())
            binder.bind(EmailInvitationAdapter, MagicMock())
            binder.bind(TokenAdapter, MagicMock())
            binder.bind(PhoenixServerConfig, self._server_config)
            binder.bind(AuthorizationRepository, MagicMock())
            binder.bind(OrganizationRepository, self.org_repo)

        inject.clear_and_configure(config=configure_with_binder)

    @patch(
        f"{ADMIN_INVITATION_USE_CASE_PATH}.invitation_should_be_sent",
        MagicMock(return_value=True),
    )
    @patch(f"{ADMIN_INVITATION_USE_CASE_PATH}._invite")
    @patch(f"{ADMIN_INVITATION_REQ_OBJ_PATH}.INVITATION_PERMISSIONS_PER_ROLE")
    def test_retrieve_org_when_organization_id_passed(self, permissions, invite):
        permissions.get.return_value = [RoleName.ORGANIZATION_STAFF]
        user = MagicMock(spec_set=AuthorizedUser)
        email = "test@huma.com"
        invitation_dict = {
            SendAdminInvitationsRequestObject.CLIENT_ID: CLIENT_ID,
            SendAdminInvitationsRequestObject.PROJECT_ID: PROJECT_ID,
            SendAdminInvitationsRequestObject.ROLE_ID: RoleName.ORGANIZATION_STAFF,
            SendAdminInvitationsRequestObject.EMAILS: [email],
            SendAdminInvitationsRequestObject.ORGANIZATION_ID: SAMPLE_ID,
            SendAdminInvitationsRequestObject.SUBMITTER: user,
        }
        req_obj = SendAdminInvitationsRequestObject.from_dict(invitation_dict)
        SendAdminInvitationsUseCase().execute(req_obj)
        self.org_repo.retrieve_organization.assert_called_with(
            organization_id=SAMPLE_ID
        )
        invite.assert_called_with(email, self.org_repo.retrieve_organization().name)


class ValidateInvitationUseCaseTestCase(unittest.TestCase):
    def setUp(self):
        self.invitation_repo = MagicMock()
        self.config = MagicMock()
        self.sample_code = "sample_code"
        self.config.server.invitation.shortenedCodeLength = 16

        def configure_with_binder(binder: inject.Binder):
            binder.bind(InvitationRepository, self.invitation_repo)
            binder.bind(PhoenixServerConfig, self.config)

        inject.clear_and_configure(config=configure_with_binder)

    def _sample_validate_invitation_req_obj_dict(self):
        return {InvitationValidityRequestObject.INVITATION_CODE: self.sample_code}

    def test_success_validate_invitation_req_obj__required_field_exist(self):
        try:
            InvitationValidityRequestObject.from_dict(
                self._sample_validate_invitation_req_obj_dict()
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_validate_invitation_req_obj__required_field_missing(self):
        with self.assertRaises(ConvertibleClassValidationError):
            InvitationValidityRequestObject.from_dict({})

    @freeze_time("2012-01-01")
    def test_validate_invitation_use_case_execute(self):
        invitation = MagicMock()
        invitation.expiresAt = datetime.datetime(2022, 1, 1, 0, 0)
        self.invitation_repo.retrieve_invitation.return_value = invitation
        req_obj = InvitationValidityRequestObject.from_dict(
            self._sample_validate_invitation_req_obj_dict()
        )
        InvitationValidityUseCase().execute(req_obj)
        self.invitation_repo.retrieve_invitation.assert_called_with(
            code=self.sample_code
        )
