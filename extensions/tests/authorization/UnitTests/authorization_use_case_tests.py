from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch
from extensions.authorization.use_cases.assign_managers_to_users_use_case import (
    AssignManagersToUsersUseCase,
)

import isodate
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from redis import Redis

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role, RoleName
from extensions.authorization.models.user import (
    BoardingStatus,
    User,
    RoleAssignment,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.user_profile_request import (
    AssignManagerRequestObject,
    AssignManagersToUsersRequestObject,
    RetrieveAssignedProfilesRequestObject,
    RetrieveProfilesRequestObject,
    RetrieveFullConfigurationRequestObject,
    RetrieveUserProfileRequestObject,
    RetrieveDeploymentConfigRequestObject,
    RetrieveStaffRequestObject,
    DEFAULT_PROFILE_RESULT_PAGE_SIZE,
    RetrieveProxyInvitationsRequestObject,
    ReactivateUserRequestObject,
    ReactivateUsersRequestObject,
    UnlinkProxyRequestObject,
    RetrieveUserResourcesRequestObject,
    OffBoardUserRequestObject,
    OffBoardUsersRequestObject,
)
from extensions.authorization.use_cases.assign_manager_use_case import (
    AssignManagerUseCase,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.authorization.use_cases.offboard_users_use_case import (
    OffBoardUsersUseCase,
)
from extensions.authorization.use_cases.retrieve_assigned_profiles_use_case import (
    RetrieveAssignedProfilesUseCase,
)
from extensions.authorization.use_cases.retrieve_deployment_config_use_case import (
    RetrieveDeploymentConfigUseCase,
)
from extensions.authorization.use_cases.retrieve_full_configuration_use_case import (
    RetrieveFullConfigurationUseCase,
)
from extensions.authorization.use_cases.retrieve_profile_use_case import (
    RetrieveProfileUseCase,
)
from extensions.authorization.use_cases.retrieve_profiles_use_case import (
    RetrieveProfilesUseCase,
)
from extensions.authorization.use_cases.retrieve_proxy_invitations import (
    RetrieveProxyInvitationsUseCase,
)
from extensions.authorization.use_cases.retrieve_staff_use_case import (
    RetrieveStaffUseCase,
)
from extensions.authorization.use_cases.reactivate_user_use_case import (
    ReactivateUserUseCase,
)
from extensions.authorization.use_cases.reactivate_users_use_case import (
    ReactivateUsersUseCase,
)
from extensions.authorization.use_cases.proxy_use_cases import UnlinkProxyUserUseCase
from extensions.authorization.use_cases.retrieve_user_resources_use_case import (
    RetrieveUserResourcesUseCase,
)
from extensions.deployment.models.deployment import (
    Deployment,
    ExtraCustomFieldConfig,
    ReasonDetails,
)
from extensions.deployment.models.status import EnableStatus, Status
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.exceptions import UserWithdrewEconsent
from extensions.module_result.models.module_config import ModuleConfig, StaticEvent
from extensions.module_result.models.primitives import Weight
from extensions.module_result.repository.custom_module_config_repository import (
    CustomModuleConfigRepository,
)
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.caching.repo.caching_repo import CachingRepository
from sdk.common.exceptions.exceptions import (
    UserAlreadyActiveException,
    UserAlreadyOffboardedException,
)
from sdk.common.localization.utils import Localization
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.versioning.models.version import Version

USE_CASE_ROUTE = "extensions.authorization.use_cases"
SAMPLE_DEPLOYMENT_ID = "5fe0a9c0d4696db1c7cd759a"
SAMPLE_USER_ID = "5fe0a9c0d4696db1c7cd759a"
SAMPLE_CONFIG_ID = "5fe0a9c0d4696db1c7cd759c"
SAMPLE_PROXY_ID = "5fe0a9c0d4696db1c7cd759p"
SAMPLE_DETAILS_OFF_BOARDED = ReasonDetails.RECOVERED
ACTIVE_USER = User.from_dict(
    {
        User.ID: SAMPLE_USER_ID,
        User.BOARDING_STATUS: {BoardingStatus.STATUS: BoardingStatus.Status.ACTIVE},
        User.FINISHED_ONBOARDING: True,
    }
)
OFF_BOARDED_USER = User.from_dict(
    {
        User.ID: SAMPLE_USER_ID,
        User.BOARDING_STATUS: {
            BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED,
        },
    }
)
OFF_BOARDED_USER_WITHDRAWN_ECONSENT = User.from_dict(
    {
        User.ID: SAMPLE_USER_ID,
        User.BOARDING_STATUS: {
            BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED,
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF,
        },
    }
)
DEPLOYMENT = Deployment.from_dict({})
SAMPLE_REQUEST_OBJECT = {
    OffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID,
    OffBoardUserRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
    OffBoardUserRequestObject.DEPLOYMENT: DEPLOYMENT,
    OffBoardUserRequestObject.DETAILS_OFF_BOARDED: SAMPLE_DETAILS_OFF_BOARDED,
}
SAMPLE_OFFBOARD_USERS_REQUEST_OBJECT = {
    OffBoardUsersRequestObject.USER_IDS: [SAMPLE_USER_ID],
    OffBoardUsersRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
    OffBoardUsersRequestObject.DEPLOYMENT: DEPLOYMENT,
    OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: SAMPLE_DETAILS_OFF_BOARDED,
}
SAMPLE_REACTIVATE_USERS_REQUEST_OBJECT = {
    ReactivateUsersRequestObject.USER_IDS: [SAMPLE_USER_ID],
    ReactivateUsersRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
    ReactivateUsersRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
}


class MockAuthUser:
    def __init__(self, user):
        self.user = user

    deployment_id = MagicMock(return_value=SAMPLE_DEPLOYMENT_ID)
    deployment_ids = MagicMock(return_value=[SAMPLE_DEPLOYMENT_ID])
    is_manager = MagicMock(return_value=True)
    get_role = MagicMock()


class MockAuthService:
    def __init__(self, repo=None):
        pass

    retrieve_user_profile = MagicMock()
    retrieve_simple_user_profile = MagicMock()
    validate_manager_ids = MagicMock()
    retrieve_user_profiles_by_ids = MagicMock(return_value="")
    retrieve_simple_user_profiles_by_ids = MagicMock(return_value="")
    update_user_profile = MagicMock()


class MockDeploymentService:
    retrieve_deployment = MagicMock(return_value=Deployment())


class MockAuthRepo:
    assign_managers_and_create_log = MagicMock()
    assign_managers_to_users = MagicMock()
    retrieve_profiles_with_assigned_manager = MagicMock()
    retrieve_assigned_managers_ids_for_multiple_users = MagicMock()
    retrieve_assigned_patients_count = MagicMock()
    retrieve_user_profiles = MagicMock(return_value=([], "hash"))
    retrieve_user_profile = MagicMock()
    retrieve_simple_user_profile = MagicMock()
    retrieve_staff = MagicMock()
    retrieve_staff.return_value = []


class MockDeploymentRepo:
    retrieve_deployment_codes = MagicMock()


class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_cache_repo = MagicMock()
        cls.mocked_cache_repo.get.return_value = None
        cls.mocked_version = Version(server="1.11.0")

        def bind(binder):
            binder.bind_to_provider(ConsentRepository, MagicMock())
            binder.bind_to_provider(EConsentRepository, MagicMock())
            binder.bind_to_provider(DeploymentRepository, MagicMock())
            binder.bind_to_provider(OrganizationRepository, MagicMock())
            binder.bind(CachingRepository, cls.mocked_cache_repo)
            binder.bind_to_provider(AuthorizationRepository, MockAuthRepo)
            binder.bind_to_provider(InvitationRepository, MagicMock())
            binder.bind(Version, cls.mocked_version)
            mocked_redis = MagicMock()
            mocked_redis.get.return_value = (
                '[{"userId": "%s"}, "hashed value"]' % SAMPLE_USER_ID
            )
            binder.bind(Redis, mocked_redis)
            binder.bind(PhoenixServerConfig, MagicMock())
            binder.bind(Localization, MagicMock())
            binder.bind_to_provider(AuthorizedUser, MockAuthUser)

        inject.clear_and_configure(bind)


class TestAssignManagerUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService",
        MockAuthService,
    )
    def test_success_assign_manager(self):
        request_object = AssignManagerRequestObject.from_dict(
            {
                "userId": "5fe07f2c0d862378d70fa19b",
                "managerIds": ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"],
                "submitterId": "5fe0a9c0d4696db1c7cd759a",
            }
        )
        AssignManagerUseCase().execute(request_object)
        MockAuthRepo.assign_managers_and_create_log.assert_called_with(
            manager_assigment=request_object
        )

    @patch(f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizedUser")
    @patch(f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService")
    def test_failure_assign_manager(self, mock_auth_service, mock_auth_user):
        manager_ids = ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"]
        deployment_id = SAMPLE_DEPLOYMENT_ID
        mock_auth_service().retrieve_user_profile = MagicMock()
        mock_auth_service().validate_manager_ids = MagicMock()
        mock_auth_service().retrieve_user_profiles_by_ids = MagicMock(
            return_value=manager_ids
        )
        mock_auth_user().deployment_id = MagicMock(return_value=deployment_id)
        mock_auth_user().deployment_ids = MagicMock(return_value=[deployment_id])
        mock_auth_user().is_manager = MagicMock(return_value=False)
        mock_auth_user().get_role = MagicMock()

        request_object = AssignManagerRequestObject.from_dict(
            {
                "userId": "5fe07f2c0d862378d70fa19b",
                "managerIds": manager_ids,
                "submitterId": "5fe0a9c0d4696db1c7cd759a",
            }
        )
        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagerUseCase().execute(request_object)

    @patch(f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizedUser")
    @patch(f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService")
    def test_validate_manager_ids(self, mock_auth_service, mock_auth_user):
        manager_ids = ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"]
        deployment_id = SAMPLE_DEPLOYMENT_ID
        mock_auth_service().validate_manager_ids = MagicMock()
        mock_auth_service().retrieve_user_profiles_by_ids = MagicMock(
            return_value=manager_ids
        )
        mock_auth_user().is_manager = MagicMock(return_value=True)
        mock_auth_user().deployment_id = MagicMock(return_value=deployment_id)
        mock_auth_user().deployment_ids = MagicMock(return_value=[deployment_id])
        mock_auth_user().get_role = MagicMock()

        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagerUseCase().validate_manager_ids("invalid", manager_ids)

    def test_validate_manager_ids_with_empty_ids(self):
        try:
            AssignManagerUseCase().validate_manager_ids(SAMPLE_DEPLOYMENT_ID, [])
        except ConvertibleClassValidationError:
            self.fail()


class TestAssignManagersToUsersUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.assign_managers_to_users_use_case.AuthorizationService",
        MockAuthService,
    )
    def test_success_assign_manager(self):
        user_ids = ["5fe07f2c0d862378d70fa19b", "5fe07f2c0d862378d70fa123"]
        manager_ids = ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"]
        submitter_id = "5fe0a9c0d4696db1c7cd759a"
        request_object = AssignManagersToUsersRequestObject.from_dict(
            {
                "userIds": user_ids,
                "managerIds": manager_ids,
                "submitterId": submitter_id,
            }
        )
        AssignManagersToUsersUseCase().execute(request_object)
        MockAuthRepo.assign_managers_to_users.assert_called_with(
            manager_ids=manager_ids, user_ids=user_ids, submitter_id=submitter_id
        )

    @patch(f"{USE_CASE_ROUTE}.assign_managers_to_users_use_case.AuthorizedUser")
    @patch(f"{USE_CASE_ROUTE}.assign_managers_to_users_use_case.AuthorizationService")
    def test_failure_assign_manager(self, mock_auth_service, mock_auth_user):
        manager_ids = ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"]
        deployment_id = SAMPLE_DEPLOYMENT_ID
        mock_auth_service().retrieve_simple_user_profile = MagicMock()
        mock_auth_service().validate_user_ids = MagicMock()
        mock_auth_service().retrieve_simple_user_profiles_by_ids = MagicMock(
            return_value=manager_ids
        )
        mock_auth_user().deployment_id = MagicMock(return_value=deployment_id)
        mock_auth_user().deployment_ids = MagicMock(return_value=[deployment_id])
        mock_auth_user().is_manager = MagicMock(return_value=False)
        mock_auth_user().get_role = MagicMock()

        request_object = AssignManagersToUsersRequestObject.from_dict(
            {
                "userIds": ["5fe07f2c0d862378d70fa19b", "5fe07f2c0d862378d70fa123"],
                "managerIds": manager_ids,
                "submitterId": "5fe0a9c0d4696db1c7cd759a",
            }
        )
        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagersToUsersUseCase().execute(request_object)

    @patch(f"{USE_CASE_ROUTE}.assign_managers_to_users_use_case.AuthorizedUser")
    @patch(f"{USE_CASE_ROUTE}.assign_managers_to_users_use_case.AuthorizationService")
    def test_validate_user_ids(self, mock_auth_service, mock_auth_user):
        manager_ids = ["5fe0a9b2e9023cb3d8c3ee8b", "5fe0a9b9f55dff5e2406b72b"]
        deployment_id = SAMPLE_DEPLOYMENT_ID
        mock_auth_service().validate_user_ids = MagicMock()
        mock_auth_service().retrieve_simple_user_profiles_by_ids = MagicMock(
            return_value=manager_ids
        )
        mock_auth_user().is_manager = MagicMock(return_value=True)
        mock_auth_user().deployment_id = MagicMock(return_value=deployment_id)
        mock_auth_user().deployment_ids = MagicMock(return_value=[deployment_id])
        mock_auth_user().get_role = MagicMock()

        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagersToUsersUseCase().validate_user_ids(
                "invalid", manager_ids, Role.UserType.MANAGER
            )

    def test_validate_user_ids_with_empty_ids(self):
        try:
            AssignManagersToUsersUseCase().validate_user_ids(
                SAMPLE_DEPLOYMENT_ID, [], Role.UserType.MANAGER
            )
        except ConvertibleClassValidationError:
            self.fail()


class TestRetrieveAssignedProfilesUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService",
        MockAuthService,
    )
    def test_success_retrieve_assigned_profiles(self):
        request_object = RetrieveAssignedProfilesRequestObject.from_dict(
            {"managerId": "5fe07f2c0d862378d70fa19b"}
        )
        RetrieveAssignedProfilesUseCase().execute(request_object)
        MockAuthRepo.retrieve_profiles_with_assigned_manager.assert_called_with(
            "5fe07f2c0d862378d70fa19b"
        )


class TestRetrieveProfileUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.retrieve_profile_use_case.AuthorizationService",
        MockAuthService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.retrieve_profile_use_case.DeploymentService",
        MockDeploymentService,
    )
    def test_success_retrieve_profile_use_case(self):
        MockAuthService.retrieve_user_profile.return_value = User.from_dict(
            {
                User.ID: "5ed803dd5f2f99da73684412",
                User.GIVEN_NAME: "test",
                User.FAMILY_NAME: "hey",
                User.GENDER: "MALE",
                User.TIMEZONE: "UTC",
            }
        )
        data = {
            RetrieveUserProfileRequestObject.USER_ID: SAMPLE_USER_ID,
            RetrieveUserProfileRequestObject.CAN_VIEW_IDENTIFIER_DATA: False,
            RetrieveUserProfileRequestObject.IS_MANAGER: True,
        }

        request_object = RetrieveUserProfileRequestObject.from_dict(data)
        response = RetrieveProfileUseCase().execute(request_object)

        MockAuthService.retrieve_user_profile.assert_called_with(
            user_id=request_object.userId, is_manager_request=request_object.isManager
        )

        self.assertNotIn(User.GIVEN_NAME, response.value)
        self.assertNotIn(User.FAMILY_NAME, response.value)

        data[RetrieveUserProfileRequestObject.CAN_VIEW_IDENTIFIER_DATA] = True
        request_object = RetrieveUserProfileRequestObject.from_dict(data)
        response = RetrieveProfileUseCase().execute(request_object)

        self.assertIn(User.GIVEN_NAME, response.value)
        self.assertIn(User.FAMILY_NAME, response.value)


class TestRetrieveProfilesUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService",
        MockAuthService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.retrieve_profiles_use_case.DeploymentService",
        MockDeploymentService,
    )
    def test_success_retrieve_profiles_use_case(self):
        request_object = RetrieveProfilesRequestObject.from_dict(
            {
                RetrieveProfilesRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                RetrieveProfilesRequestObject.SUBMITTER: AuthorizedUser(User()),
            }
        )
        RetrieveProfilesUseCase().execute(request_object)
        MockAuthRepo.retrieve_assigned_managers_ids_for_multiple_users.assert_called_with(
            set()
        )
        MockAuthRepo.retrieve_user_profiles.assert_called_with(
            SAMPLE_DEPLOYMENT_ID,
            search=None,
            role=Role.UserType.USER,
            sort=[],
            skip=0,
            limit=DEFAULT_PROFILE_RESULT_PAGE_SIZE,
            search_ignore_keys=[User.NHS, User.GIVEN_NAME, User.FAMILY_NAME],
            manager_id=None,
            filters=None,
            enabled_module_ids=None,
            sort_extra=None,
        )

    @patch(
        f"{USE_CASE_ROUTE}.assign_manager_use_case.AuthorizationService",
        MockAuthService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.retrieve_profiles_use_case.DeploymentService",
        MockDeploymentService,
    )
    def test_success_retrieve_profiles_use_case_with_view_identifier(self):
        MockAuthRepo.retrieve_user_profiles.return_value = (
            [
                User.from_dict(
                    {
                        User.ID: "5ed803dd5f2f99da73684412",
                        User.GIVEN_NAME: "test",
                        User.FAMILY_NAME: "hey",
                        User.GENDER: "MALE",
                        User.TIMEZONE: "UTC",
                    }
                )
            ],
            "hash",
        )

        data = {
            RetrieveProfilesRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            RetrieveProfilesRequestObject.CAN_VIEW_IDENTIFIER_DATA: False,
            RetrieveProfilesRequestObject.CLEAN: True,
            RetrieveProfilesRequestObject.SUBMITTER: AuthorizedUser(User()),
        }
        request_object = RetrieveProfilesRequestObject.from_dict(data)
        response = RetrieveProfilesUseCase().execute(request_object)

        for user in response.value:
            self.assertNotIn(User.GIVEN_NAME, user)
            self.assertNotIn(User.FAMILY_NAME, user)

        data[RetrieveProfilesRequestObject.CAN_VIEW_IDENTIFIER_DATA] = True
        request_object = RetrieveProfilesRequestObject.from_dict(data)
        response = RetrieveProfilesUseCase().execute(request_object)

        for user in response.value:
            self.assertIn(User.GIVEN_NAME, user)
            self.assertIn(User.FAMILY_NAME, user)


DEPLOYMENT_IDS = [
    "5d386cc6ff885918d96edb2c",
    "5ed8ae76cf99540b259a7315",
]


class MockOrganizationRepo:
    retrieve_organizations = MagicMock(
        return_value=(
            [
                Organization.from_dict(
                    {
                        Organization.NAME: "ABC Pharmaceuticals EU Trials 123",
                        Organization.DEPLOYMENT_IDS: DEPLOYMENT_IDS,
                        Organization.ENROLLMENT_TARGET: 3000,
                        Organization.STUDY_COMPLETION_TARGET: 2800,
                        Organization.STATUS: Status.DEPLOYED.value,
                    }
                )
            ],
            1,
        )
    )


class TestRetrieveFullConfigurationUseCase(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MockAuthRepo()
        self.deployment_repo = MagicMock()
        self.organization_repo = MockOrganizationRepo()

    def test_success_retrieve_full_configuration_use_case(self):
        user = MagicMock()
        user.organization_ids.return_value = []
        user.deployment_ids.return_value = DEPLOYMENT_IDS
        request_object = RetrieveFullConfigurationRequestObject(user=user)
        RetrieveFullConfigurationUseCase(
            repo=self.auth_repo,
            deployment_repo=self.deployment_repo,
            organization_repo=self.organization_repo,
        ).execute(request_object)

        self.organization_repo.retrieve_organizations.assert_not_called()
        self.deployment_repo.retrieve_deployments_by_ids.assert_called_with(
            DEPLOYMENT_IDS
        )


class TestRetrieveConfigurationUseCase(TestCase):
    def configure(self, event):
        auth_repo = MockAuthRepo()
        deployment_repo = MagicMock()
        self.config = ModuleConfig(
            staticEvent=event, status=EnableStatus.ENABLED, moduleId=Weight.__name__
        )
        custom_field = {
            "test": ExtraCustomFieldConfig.from_dict(
                {
                    ExtraCustomFieldConfig.ERROR_MESSAGE: "Test error",
                    ExtraCustomFieldConfig.ONBOARDING_COLLECTION_TEXT: "Test collection",
                    ExtraCustomFieldConfig.DESCRIPTION: "Test description",
                    ExtraCustomFieldConfig.ORDER: 1,
                    ExtraCustomFieldConfig.PROFILE_COLLECTION_TEXT: "Test",
                    ExtraCustomFieldConfig.TYPE: "TEXT",
                    ExtraCustomFieldConfig.VALIDATION: "^.{10}$",
                }
            )
        }
        self.extra_custom_fields = custom_field
        deployment = Deployment(
            id=SAMPLE_DEPLOYMENT_ID,
            moduleConfigs=[self.config],
            extraCustomFields=self.extra_custom_fields,
        )
        deployment_repo.retrieve_deployment.return_value = deployment
        deployment_repo.retrieve_localization.return_value = {}

        config = MagicMock()
        config.server.moduleResult.applyDefaultDisclaimerConfig = False

        def configure_with_binder(binder: Binder):
            binder.bind(AuthRepository, auth_repo)
            binder.bind(DeploymentRepository, deployment_repo)
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(CustomModuleConfigRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(FileStorageAdapter, MagicMock())
            binder.bind(PhoenixServerConfig, config)
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

        self.now = datetime.utcnow()
        roles = [
            RoleAssignment(
                roleId=RoleName.USER,
                resource=f"deployment/{SAMPLE_DEPLOYMENT_ID}",
            )
        ]
        user = User(
            id=SAMPLE_USER_ID,
            roles=roles,
            createDateTime=self.now,
            finishedOnboarding=True,
        )
        self.authorized_user = AuthorizedUser(user)

    def test_success_retrieve_static_event_configuration_use_case(self):
        static_event = StaticEvent(enabled=True, title="test", description="test")
        self.configure(static_event)

        request_data = {
            RetrieveDeploymentConfigRequestObject.USER: self.authorized_user
        }
        request_object = RetrieveDeploymentConfigRequestObject.from_dict(request_data)
        use_case = RetrieveDeploymentConfigUseCase()

        resp = use_case.execute(request_object).value
        self.assertEqual(1, len(resp.moduleConfigs))
        self.assertEqual(self.config, resp.moduleConfigs[0])

    def test_static_event_configuration__expired(self):
        # configuring expirable event, and checking if expired after 3 month
        duration = "P3M"
        static_event = StaticEvent(
            enabled=True, title="test", description="test", isoDuration=duration
        )

        self.configure(static_event)

        request_data = {
            RetrieveDeploymentConfigRequestObject.USER: self.authorized_user
        }
        request_object = RetrieveDeploymentConfigRequestObject.from_dict(request_data)
        duration = isodate.parse_duration(duration)
        use_case = RetrieveDeploymentConfigUseCase()
        expired_date = self.now + duration

        with freeze_time(expired_date - relativedelta(minutes=1)):
            resp = use_case.execute(request_object).value
        self.assertEqual(1, len(resp.moduleConfigs))

        with freeze_time(self.now + duration):
            resp = use_case.execute(request_object).value
        self.assertEqual(0, len(resp.moduleConfigs))

    def test_static_event_configuration__disabled(self):
        # configuring expirable event, and checking if expired after 3 month
        duration = "P3M"
        static_event = StaticEvent(
            enabled=False, title="test", description="test", isoDuration=duration
        )

        self.configure(static_event)

        request_data = {
            RetrieveDeploymentConfigRequestObject.USER: self.authorized_user
        }
        request_object = RetrieveDeploymentConfigRequestObject.from_dict(request_data)
        duration = isodate.parse_duration(duration)
        use_case = RetrieveDeploymentConfigUseCase()

        not_expired_date = self.now + duration - relativedelta(minutes=1)

        with freeze_time(not_expired_date):
            resp = use_case.execute(request_object).value
        self.assertEqual(0, len(resp.moduleConfigs))


class TestRetrieveStaffUseCase(TestCase):
    def test_success_retrieve_staff(self):
        request_obj = RetrieveStaffRequestObject(
            organizationId="608186cbd2a26d5c4858166b", submitter=MockAuthUser
        )
        RetrieveStaffUseCase(
            repo=MockAuthRepo, deployment_repo=MockDeploymentRepo
        ).execute(request_obj)
        MockAuthRepo.retrieve_assigned_patients_count.assert_called_once()
        MockAuthRepo.retrieve_staff.assert_called_once()
        MockDeploymentRepo.retrieve_deployment_codes.assert_called_once()


class TestRetrieveProxyInvitationsUseCase(BaseTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.retrieve_proxy_invitations.RetrieveProxyInvitationsResponseObject"
    )
    @patch(f"{USE_CASE_ROUTE}.base_authorization_use_case.AuthorizationRepository")
    @patch(f"{USE_CASE_ROUTE}.retrieve_proxy_invitations.InvitationRepository")
    def test_retrieve_proxy_invitations(self, invitation_repo, auth_repo, rsp_obj):
        roles = [
            RoleAssignment(
                roleId=RoleName.PROXY,
                resource=f"deployment/{SAMPLE_DEPLOYMENT_ID}",
            )
        ]
        user = User(
            id=SAMPLE_USER_ID,
            roles=roles,
        )
        self.authorized_user = AuthorizedUser(user)
        self.invitation_repo = invitation_repo
        self.auth_repo = auth_repo

        request_obj = RetrieveProxyInvitationsRequestObject.from_dict(
            {RetrieveProxyInvitationsRequestObject.SUBMITTER: self.authorized_user}
        )

        RetrieveProxyInvitationsUseCase(
            invitation_repo=self.invitation_repo, auth_repo=self.auth_repo
        ).execute(request_obj)
        self.invitation_repo.retrieve_proxy_invitation.assert_called_with(
            user_id=self.authorized_user.id
        )
        rsp_obj.assert_called_once()


class TestReactivateUserUseCase(TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()
        self._event_bus = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(AuthorizationRepository, self._repo)
            binder.bind(EventBusAdapter, self._event_bus)

        inject.clear_and_configure(configure_binder)

    @patch(f"{USE_CASE_ROUTE}.reactivate_user_use_case.PostUserReactivationEvent")
    def test_success_reactivate_user(self, mock_event):
        request_obj = ReactivateUserRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

        self._repo.retrieve_simple_user_profile.return_value = OFF_BOARDED_USER

        ReactivateUserUseCase().execute(request_obj)

        self._repo.update_user_profile.assert_called_once()
        mock_event.assert_called_with(self._repo.update_user_profile())

    @patch(f"{USE_CASE_ROUTE}.reactivate_user_use_case.PostUserReactivationEvent")
    def test_failure_reactivate_user(self, mock_event):
        request_obj = ReactivateUserRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

        self._repo.retrieve_simple_user_profile.return_value = ACTIVE_USER
        with self.assertRaises(UserAlreadyActiveException):
            ReactivateUserUseCase().execute(request_obj)
            mock_event.assert_not_called()

    @patch(f"{USE_CASE_ROUTE}.reactivate_user_use_case.PostUserReactivationEvent")
    def test_failure_reactivate_user_withdrawn_econsent(self, mock_event):
        request_obj = ReactivateUserRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

        self._repo.retrieve_simple_user_profile.return_value = (
            OFF_BOARDED_USER_WITHDRAWN_ECONSENT
        )
        with self.assertRaises(UserWithdrewEconsent):
            ReactivateUserUseCase().execute(request_obj)
            mock_event.assert_not_called()


class TestOffboardUserUseCase(TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()
        self._event_bus = MagicMock()
        self.deployment_repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(AuthorizationRepository, self._repo)
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(EventBusAdapter, self._event_bus)
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(configure_binder)

    @patch(f"{USE_CASE_ROUTE}.off_board_user_use_case.PostUserOffBoardEvent")
    def test_success_off_board_user(self, mock_event):
        request_obj = OffBoardUserRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

        self._repo.retrieve_simple_user_profile.return_value = ACTIVE_USER

        OffBoardUserUseCase().execute(request_obj)

        self._repo.update_user_profile.assert_called_once()
        mock_event.assert_called_with(
            self._repo.update_user_profile(), SAMPLE_DETAILS_OFF_BOARDED
        )

    @patch(f"{USE_CASE_ROUTE}.off_board_user_use_case.PostUserOffBoardEvent")
    def test_failure_off_board_user(self, mock_event):
        request_obj = OffBoardUserRequestObject.from_dict(SAMPLE_REQUEST_OBJECT)

        self._repo.retrieve_simple_user_profile.return_value = OFF_BOARDED_USER
        with self.assertRaises(UserAlreadyOffboardedException):
            OffBoardUserUseCase().execute(request_obj)
            mock_event.assert_not_called()


class TestOffboardUsersUseCase(TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()
        self._event_bus = MagicMock()
        self.deployment_repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(AuthorizationRepository, self._repo)
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(EventBusAdapter, self._event_bus)
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(configure_binder)

    @patch(f"{USE_CASE_ROUTE}.offboard_users_use_case.PostUserOffBoardEvent")
    def test_success_offboard_users(self, mock_event):
        request_obj = OffBoardUsersRequestObject.from_dict(
            SAMPLE_OFFBOARD_USERS_REQUEST_OBJECT
        )

        self._repo.retrieve_simple_user_profiles_by_ids.return_value = [ACTIVE_USER]

        OffBoardUsersUseCase().execute(request_obj)

        self._repo.update_user_profiles.assert_called_once()
        mock_event.assert_called_with(SAMPLE_USER_ID, SAMPLE_DETAILS_OFF_BOARDED)

    @patch(f"{USE_CASE_ROUTE}.offboard_users_use_case.PostUserOffBoardEvent")
    def test_failure_offboard_users(self, mock_event):
        request_obj = OffBoardUsersRequestObject.from_dict(
            SAMPLE_OFFBOARD_USERS_REQUEST_OBJECT
        )

        self._repo.retrieve_simple_user_profiles_by_ids.return_value = [
            OFF_BOARDED_USER
        ]
        with self.assertRaises(UserAlreadyOffboardedException):
            OffBoardUsersUseCase().execute(request_obj)
            mock_event.assert_not_called()


class TestReactivateUsersUseCase(TestCase):
    def setUp(self) -> None:
        self._repo = MagicMock()
        self._event_bus = MagicMock()
        self.deployment_repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(AuthorizationRepository, self._repo)
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(EventBusAdapter, self._event_bus)

        inject.clear_and_configure(configure_binder)

    @patch(f"{USE_CASE_ROUTE}.reactivate_users_use_case.PostUserReactivationEvent")
    def test_success_reactivate_users(self, mock_event):
        request_obj = ReactivateUsersRequestObject.from_dict(
            SAMPLE_REACTIVATE_USERS_REQUEST_OBJECT
        )

        self._repo.retrieve_simple_user_profiles_by_ids.return_value = [
            OFF_BOARDED_USER
        ]

        ReactivateUsersUseCase().execute(request_obj)

        self._repo.update_user_profiles.assert_called_once()
        mock_event.assert_called_with(SAMPLE_USER_ID)

    @patch(f"{USE_CASE_ROUTE}.reactivate_users_use_case.PostUserReactivationEvent")
    def test_failure_reactivate_users(self, mock_event):
        request_obj = ReactivateUsersRequestObject.from_dict(
            SAMPLE_REACTIVATE_USERS_REQUEST_OBJECT
        )

        self._repo.retrieve_simple_user_profiles_by_ids.return_value = [ACTIVE_USER]
        with self.assertRaises(UserAlreadyActiveException):
            ReactivateUsersUseCase().execute(request_obj)
            mock_event.assert_not_called()

    @patch(f"{USE_CASE_ROUTE}.reactivate_users_use_case.PostUserReactivationEvent")
    def test_failure_reactivate_users_withdrawn_econsent(self, mock_event):
        request_obj = ReactivateUsersRequestObject.from_dict(
            SAMPLE_REACTIVATE_USERS_REQUEST_OBJECT
        )

        self._repo.retrieve_simple_user_profiles_by_ids.return_value = [
            OFF_BOARDED_USER_WITHDRAWN_ECONSENT
        ]
        with self.assertRaises(UserWithdrewEconsent):
            ReactivateUsersUseCase().execute(request_obj)
            mock_event.assert_not_called()


class TestUnlinkProxyUserUseCase(TestCase):
    def setUp(self) -> None:
        self.invitation_repo = MagicMock()
        self._event_bus = MagicMock()
        self.auth_repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(InvitationRepository, self.invitation_repo)
            binder.bind(EventBusAdapter, self._event_bus)
            binder.bind(AuthorizationRepository, self.auth_repo)
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())

        inject.clear_and_configure(configure_binder)

    @patch(f"{USE_CASE_ROUTE}.proxy_use_cases.PostUnlinkProxyUserEvent")
    def test_success_unlink_proxy_user(self, mock_event):
        request_obj = UnlinkProxyRequestObject.from_dict(
            {
                UnlinkProxyRequestObject.USER_ID: SAMPLE_USER_ID,
                UnlinkProxyRequestObject.PROXY_ID: SAMPLE_USER_ID,
            }
        )
        UnlinkProxyUserUseCase().execute(request_obj)
        self.auth_repo.retrieve_simple_user_profile.assert_called_with(
            user_id=request_obj.proxyId
        )
        self.auth_repo.update_user_profile.assert_called_with(
            self.auth_repo.retrieve_simple_user_profile()
        )
        self.invitation_repo.retrieve_proxy_invitation.assert_called_with(
            user_id=request_obj.userId
        )
        self.invitation_repo.delete_invitation.assert_called_with(
            self.invitation_repo.retrieve_proxy_invitation().id
        )
        mock_event.assert_called_with(request_obj.proxyId)


class RetrieveUserResourcesUseCaseTestCase(TestCase):
    def setUp(self) -> None:
        self.auth_repo = MagicMock()
        self.deployment_repo = MagicMock()
        self.org_repo = MagicMock()

        def configure_binder(binder: inject.Binder):
            binder.bind(AuthorizationRepository, self.auth_repo)
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(OrganizationRepository, self.org_repo)

        inject.clear_and_configure(configure_binder)

    @patch(
        "extensions.authorization.use_cases.retrieve_user_resources_use_case.AuthorizedUser"
    )
    def test_success_execute_retrieve_user_resources(self, authz_user):
        req_obj = RetrieveUserResourcesRequestObject.from_dict(
            {RetrieveUserResourcesRequestObject.USER_ID: SAMPLE_USER_ID}
        )
        RetrieveUserResourcesUseCase().execute(req_obj)
        authz_user().deployment_ids.assert_called_once()
        self.auth_repo.retrieve_simple_user_profile.assert_called_with(
            user_id=SAMPLE_USER_ID
        )
        self.deployment_repo.retrieve_deployments_by_ids.assert_called_with(
            deployment_ids=[]
        )
        self.org_repo.retrieve_organizations_by_ids.assert_called_with(
            organization_ids=authz_user().organization_ids()
        )
