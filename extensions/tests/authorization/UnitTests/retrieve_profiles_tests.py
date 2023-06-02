from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
    RetrieveUserProfileRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveProfileResponseObject,
)
from extensions.authorization.use_cases.retrieve_profile_use_case import (
    RetrieveProfileUseCase,
)
from extensions.authorization.use_cases.retrieve_profiles_use_case import (
    RetrieveProfilesUseCase,
)
from extensions.deployment.repository.consent_repository import ConsentRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.caching.repo.caching_repo import CachingRepository
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.tests.auth.test_helpers import USER_ID

used_ids = []

AUTH_USE_CASE_PATH = "extensions.authorization.use_cases"


def check_id(func):
    def wrapper(user_id):
        if user_id in used_ids:
            raise Exception("Id Already taken")
        user = func(user_id)
        used_ids.append(user.id)
        return user

    return wrapper


@check_id
def get_manager(user_id):
    role = RoleAssignment.create_role(RoleName.ADMIN, "test")
    return User(id=user_id, roles=[role])


@check_id
def get_user(user_id):
    role = RoleAssignment.create_role(RoleName.USER, "test")
    return User(id=user_id, roles=[role])


class MockRepo:
    def retrieve_assigned_managers_ids_for_multiple_users(self, ids):
        result = {id_: [] for id_ in ids}
        result.update({"1": ["2"]})
        return result

    def retrieve_assigned_patients_count(self):
        return {"1": 2, "2": 5}


class RetrieveProfilesTests(TestCase):
    def setUp(self) -> None:
        global used_ids
        used_ids = []

        def configure_with_binder(binder: Binder):
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(OrganizationRepository, MagicMock())
            binder.bind(AuthorizationRepository, MagicMock())
            binder.bind(ConsentRepository, MagicMock())
            binder.bind(EConsentRepository, MagicMock())
            binder.bind(CachingRepository, MagicMock())

        inject.clear_and_configure(config=configure_with_binder)

    def test_preprocess_for_managers(self):
        use_case = RetrieveProfilesUseCase(MockRepo())
        users = [get_manager("1"), get_manager("2")]
        request_object = RetrieveProfilesRequestObject(
            role="Admin", deploymentId="test"
        )
        use_case.request_object = request_object
        use_case.preprocess(users)
        for user in users:
            self.assertFalse(hasattr(user, "assignedManagers"))
            self.assertTrue(hasattr(user, "assignedUsersCount"))
            if user.id == "1":
                self.assertEqual(2, user.assignedUsersCount)
            elif user.id == "2":
                self.assertEqual(5, user.assignedUsersCount)

    def test_preprocess_for_users(self):
        use_case = RetrieveProfilesUseCase(MockRepo())
        users = [get_user("1"), get_user("2")]
        request_object = RetrieveProfilesRequestObject(deploymentId="test")
        use_case.request_object = request_object
        use_case.preprocess(users)
        for user in users:
            self.assertTrue(hasattr(user, "assignedManagers"))

    @patch(f"{AUTH_USE_CASE_PATH}.retrieve_profile_use_case.AuthorizationService")
    @patch(
        f"{AUTH_USE_CASE_PATH}.retrieve_profile_use_case.AuthorizedUser.get_assigned_proxies"
    )
    @patch(
        f"{AUTH_USE_CASE_PATH}.retrieve_profile_use_case.AuthorizedUser.get_assigned_participants"
    )
    def test_assigned_proxies_present(
        self, mocked_proxies, mocked_participants, mocked_auth_service
    ):
        simple_user = User(id=USER_ID)
        mocked_participants.return_value = [1]
        mocked_proxies.return_value = [1]

        mocked_auth_service().retrieve_user_profile.return_value = simple_user

        request_data = {RetrieveUserProfileRequestObject.USER_ID: USER_ID}
        request_object = RetrieveUserProfileRequestObject.from_dict(request_data)
        use_case = RetrieveProfileUseCase(MagicMock())
        res = use_case.execute(request_object).value
        self.assertIn(RetrieveProfileResponseObject.ASSIGNED_PROXIES, res)
        self.assertIn(RetrieveProfileResponseObject.ASSIGNED_PARTICIPANTS, res)
