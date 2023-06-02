import uuid
from datetime import datetime
from functools import reduce
from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.authorization.models.role.role import Role
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.services.authorization import AuthorizationService
from extensions.common.exceptions import (
    InvalidModuleForPreferredUnitException,
    InvalidMeasureUnitException,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.module_result.models.primitives.primitive import MeasureUnit
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.authorization.UnitTests.test_helpers import MockInject
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject

SUBMITTER_DEPLOYMENT_ID = "5ff5b1059ba9a480d78481ef"

AUTH_PATH = "extensions.authorization.services.authorization"
DEP_SERVICE_PATH = "extensions.deployment.service.deployment_service.DeploymentService"
MODULE_MANAGER_PATH = "extensions.module_result.modules.modules_manager"
USER_ID = "5ff5b116f77810fc2d0057a1"
TAGS_AUTHOR_ID = "5ff5b116f77810fc2d0057b2"
MOCK_DICT = {"a": "b"}


class MockDeploymentService(MagicMock):
    retrieve_deployment = MagicMock(
        return_value=Deployment(
            roles=[
                Role(
                    name="User",
                    permissions=[
                        "VIEW_PATIENT_IDENTIFIER",
                        "VIEW_PATIENT_DATA",
                        "MANAGE_PATIENT_DATA",
                    ],
                )
            ]
        )
    )


def sample_user():
    return User(
        id="5ff5b116f77810fc2d0057a1",
        email="test@test.com",
        recentModuleResults=MOCK_DICT,
    )


def user_with_permissions():
    u = sample_user()
    u.roles = [
        RoleAssignment(roleId="User", resource="deployment/5ff5b1059ba9a480d78481ef")
    ]
    return u


class MockAuthRepo(MagicMock):
    retrieve_user = MagicMock(return_value=user_with_permissions())
    retrieve_assigned_managers_ids = MagicMock(
        return_value=User(
            id="5ff5b1230a4f3bb42a6cd195",
            email="contributor_test@test.com",
            roles=[
                RoleAssignment(
                    roleId="Contributor", resource="deployment/5ff5b1059ba9a480d78481ef"
                )
            ],
        )
    )
    update_user_profile = MagicMock(return_value="5ff5b116f77810fc2d0057a1")


class MockAuthorizedUser(MagicMock):
    is_contributor = MagicMock(return_value=True)
    is_admin = MagicMock(return_value=True)
    is_user = MagicMock(return_value=True)
    is_manager = MagicMock(return_value=False)
    deployment_role = MagicMock()
    deployment_id = MagicMock(return_value=SUBMITTER_DEPLOYMENT_ID)


class PrimitiveMock(MagicMock):
    instance = MagicMock()
    id = uuid.uuid4()
    userId = USER_ID
    moduleId = "TestModule"
    moduleConfigId = "testConfigId"
    class_name = "TestClass"
    createDateTime = None


class AuthorizationServiceTests(TestCase):
    @patch(DEP_SERVICE_PATH)
    @patch(f"{AUTH_PATH}.inject", MockInject)
    @patch(f"{AUTH_PATH}.AuthorizedUser", MockAuthorizedUser)
    def setUp(self, deployment_service):
        self.event_bus = MagicMock()
        self.repo = MagicMock()
        self.service = AuthorizationService(self.repo, self.event_bus)
        self.deployment_service = deployment_service

        def bind(binder):
            binder.bind(DeploymentRepository, MagicMock())
            binder.bind(AuthorizationRepository, self.repo)
            binder.bind(EventBusAdapter, self.event_bus)

        inject.clear_and_configure(bind)

    @patch(f"{AUTH_PATH}.inject", MockInject)
    @patch(DEP_SERVICE_PATH, MockDeploymentService)
    @patch(f"{AUTH_PATH}.check_role_id_valid_for_resource")
    def test_success_update_roles(self, check_role_valid_mock):
        self.service = AuthorizationService(repo=MockAuthRepo())
        role = RoleAssignment(
            roleId="5ff5b1059ba9a480d78481ef",
            resource="deployment/5ff5b1059ba9a480d78481ef",
        )
        check_role_valid_mock.return_value = True
        res = self.service.update_user_roles("5ff5b116f77810fc2d0057a1", [role])
        self.assertEqual(res, "5ff5b116f77810fc2d0057a1")

    @patch(f"{AUTH_PATH}.AuthorizedUser", MockAuthorizedUser)
    def test__assign_enrollment_id(self):
        user = session = MagicMock()
        self.service._assign_enrollment_id(user, session)
        self.deployment_service().update_enrollment_counter.assert_called_once_with(
            deployment_id=SUBMITTER_DEPLOYMENT_ID, session=session
        )

    @patch(f"{AUTH_PATH}.AuthorizationService._post_create_user")
    def test_create_user(self, post_create_user):
        user = session = MagicMock()
        self.service.create_user(user, session)
        self.repo.create_user.assert_called_once_with(user, session=session)
        post_create_user.assert_called_with(user)

    @patch(f"{AUTH_PATH}.PostCreateUserEvent")
    def test__post_create_user(self, event):
        user = MagicMock()
        self.service._post_create_user(user)
        self.event_bus.emit.assert_called_with(event(user))

    @patch(f"{AUTH_PATH}.PostCreateTagEvent")
    def test__post_create_tags(self, event):
        kwargs = MOCK_DICT
        self.service._post_create_tags(**kwargs)
        self.event_bus.emit.assert_called_with(event(**kwargs))

    @patch(f"{AUTH_PATH}.AuthorizationService._post_create_tags")
    def test_create_tag(self, post_create_tags):
        self.repo.create_tag = MagicMock(return_value=USER_ID)
        tags = {}
        self.service.create_tag(USER_ID, tags, TAGS_AUTHOR_ID)
        self.repo.create_tag.assert_called_once_with(USER_ID, tags, TAGS_AUTHOR_ID)
        post_create_tags.assert_called_with(
            user_id=USER_ID, tags=tags, author_id=TAGS_AUTHOR_ID
        )

    def test_retrieve_users_with_user_role_including_only_fields(self):
        required_fields = ("createDateTime", "surgeryDateTime")
        to_model = False
        self.service.retrieve_users_with_user_role_including_only_fields(
            required_fields, to_model=to_model
        )
        self.repo.retrieve_users_with_user_role_including_only_fields.assert_called_once_with(
            required_fields, to_model
        )

    @patch(f"{AUTH_PATH}.AuthorizationService._add_badges")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_recent_results_status")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_assigned_managers")
    def test_retrieve_user_profile(
        self, append_assigned_managers, recent_results_status, add_badges
    ):
        user = user_with_permissions()
        self.repo.retrieve_user.return_value = user
        self.service.retrieve_user_profile(user.id)
        append_assigned_managers.assert_called_with(user)
        recent_results_status.assert_called_once()
        add_badges.assert_called_once()

    @patch(f"{AUTH_PATH}.AuthorizationService._add_badges")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_rag_threshold")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_recent_results_status")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_assigned_managers")
    def test_retrieve_user_profile_for_manager(
        self,
        append_assigned_managers,
        recent_results_status,
        append_rag_threshold,
        add_badges,
    ):
        user = MagicMock()
        self.repo.retrieve_user.return_value = user
        self.service.retrieve_user_profile(USER_ID, is_manager_request=True)
        append_assigned_managers.assert_called_with(user)
        recent_results_status.assert_called_with(user)
        append_rag_threshold.assert_called_with(user, {})
        add_badges.assert_not_called()

    @patch(f"{AUTH_PATH}.AuthorizationService._add_badges")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_rag_threshold")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_recent_results_status")
    @patch(f"{AUTH_PATH}.AuthorizationService._append_assigned_managers")
    def test_retrieve_user_profile_for_manager_with_valid_recent_module_results(
        self,
        append_assigned_managers,
        recent_results_status,
        append_rag_threshold,
        add_badges,
    ):
        class MockUser(MagicMock):
            recentModuleResults = None

        user = MockUser()
        self.repo.retrieve_user.return_value = user
        self.assertEqual(
            self.service.retrieve_user_profile(USER_ID, is_manager_request=True), user
        )
        append_assigned_managers.assert_called_with(user)
        recent_results_status.assert_not_called()
        append_rag_threshold.assert_not_called()
        add_badges.assert_not_called()

    def test_retrieve_simple_user_profile(self):
        self.service.retrieve_simple_user_profile(USER_ID)
        self.repo.retrieve_simple_user_profile.assert_called_with(user_id=USER_ID)

    @patch(f"{AUTH_PATH}.remove_none_values", MagicMock(return_value=MOCK_DICT))
    @patch(f"{AUTH_PATH}.PostCreateAuthorizationBatchEvent")
    def test_update_covid_risk_score(self, post_create_auth_event):
        event = user = MagicMock()
        deployment_id = "5ff5b1059ba9a480d78481ab"
        post_create_auth_event.return_value = event
        self.service.update_covid_risk_score(user, deployment_id)
        post_create_auth_event.assert_called_with(
            primitives=MOCK_DICT,
            user_id=user.id,
            module_id="UpdateProfile",
            module_config_id=None,
            deployment_id=deployment_id,
            device_name=user.deviceName or "iOS",
            start_date_time=None,
        )
        self.event_bus.emit.assert_called_with(event, raise_error=True)

    def test_retrieve_user_profiles_by_ids(self):
        self.service.retrieve_user_profiles_by_ids(ids={USER_ID})
        self.repo.retrieve_user_profiles_by_ids.assert_called_with({USER_ID})

    @patch(f"{AUTH_PATH}.AuthorizationService._post_update_profile_event")
    @patch(f"{AUTH_PATH}.AuthorizationService._pre_update_profile")
    @patch(f"{AUTH_PATH}.UpdateUserProfileRequestObject")
    def test_update_user_profile(
        self, update_profile_req_obj, pre_update_profile, post_update_profile_event
    ):
        user = update_profile_req_obj
        self.service.update_user_profile(user)
        pre_update_profile.assert_called_once()
        self.repo.update_user_profile.assert_called_with(user)
        post_update_profile_event.assert_called_once()

    @patch(f"{AUTH_PATH}.inject", MockInject)
    @patch(f"{AUTH_PATH}.PostUserProfileUpdateEvent")
    def test__post_update_profile_event(self, post_update_event):
        event_bus = user = previous_state = MagicMock()
        MockInject.instance.return_value = event_bus
        self.service._post_update_profile_event(user, previous_state)
        post_update_event.assert_called_with(user, previous_state)
        self.event_bus.emit.assert_called_with(post_update_event(user, previous_state))

    @patch(f"{AUTH_PATH}.AuthorizationService.update_recent_flags")
    def test_update_recent_results(self, update_recent_flags):
        now = datetime.utcnow()
        primitive = PrimitiveMock()
        primitive.createDateTime = now

        test_user = sample_user()
        self.repo.retrieve_user.return_value = test_user
        self.service.update_recent_results([primitive])
        self.repo.retrieve_user.assert_called_with(user_id=primitive.userId)
        self.repo.update_user_profile.assert_called_with(test_user)

        results = test_user.recentModuleResults
        saved_primitive = results[primitive.moduleConfigId][0][primitive.class_name]
        self.assertEqual(primitive.id, saved_primitive.id)
        self.assertEqual(primitive.createDateTime, saved_primitive.createDateTime)
        self.assertEqual(now, test_user.lastSubmitDateTime)
        update_recent_flags.assert_called_with(test_user)

    def test_update_recent_results_with_empty_primitives(self):
        self.service.update_recent_results([])
        self.repo.retrieve_user.assert_not_called()
        self.repo.update_user_profile.assert_not_called()

    def test_delete_tag(self):
        user_id = USER_ID
        tags_author_id = TAGS_AUTHOR_ID
        self.service.delete_tag(user_id, tags_author_id)
        self.repo.delete_tag.assert_called_with(user_id, tags_author_id)

    def test_check_ip_allowed_create_super_admin(self):
        master_key = "1111"
        self.service.check_ip_allowed_create_super_admin(master_key)
        self.repo.check_ip_allowed_create_super_admin.assert_called_with(master_key)

    def test__append_assigned_managers(self):
        user = user_with_permissions()
        self.service._append_assigned_managers(user)
        self.repo.retrieve_assigned_managers_ids.assert_called_with(user.id)

    @patch(f"{AUTH_PATH}.PreUserProfileUpdateEvent")
    def test__pre_update_profile(self, pre_user_profile_update_event):
        previous_state = MagicMock()
        user = user_with_permissions()
        self.service._pre_update_profile(user, previous_state)
        pre_user_profile_update_event.assert_called_with(user, previous_state)
        self.event_bus.emit.assert_called_with(
            pre_user_profile_update_event(user, previous_state), raise_error=True
        )

    @patch(f"{AUTH_PATH}.UpdateUserProfileRequestObject")
    def test_update_user_roles(self, req_obj):
        user_id = USER_ID
        roles = MagicMock()
        self.service.update_user_roles(user_id, roles)
        self.repo.update_user_profile.assert_called_with(
            req_obj(id=user_id, roles=roles)
        )

    def test_retrieve_users_timezones(self):
        user_id = USER_ID
        self.service.retrieve_users_timezones([user_id])
        self.repo.retrieve_users_timezones.assert_called_with([user_id])

    def test_validate_user_preferred_units(self):
        preferred_units = MOCK_DICT
        with self.assertRaises(InvalidModuleForPreferredUnitException):
            self.service.validate_user_preferred_units(preferred_units)

    def test_success_validate_user_preferred_units(self):
        preferred_units_enabled_modules = (
            ModulesManager().get_preferred_unit_enabled_module_ids()
        )
        unit_value_list = MeasureUnit.get_value_list()
        preferred_units = {}
        for unit in preferred_units_enabled_modules:
            preferred_units[unit] = unit_value_list[0]
        try:
            self.service.validate_user_preferred_units(preferred_units)
        except (InvalidMeasureUnitException, InvalidModuleForPreferredUnitException):
            self.fail()

        for unit in preferred_units_enabled_modules:
            preferred_units[unit] = "invalid unit"
        with self.assertRaises(InvalidMeasureUnitException):
            self.service.validate_user_preferred_units(preferred_units)

    @patch(f"{AUTH_PATH}.inject", MockInject)
    def test_delete_user(self):
        session = MagicMock()
        self.service.delete_user(session=session, user_id=USER_ID)
        self.repo.delete_user.assert_called_with(session=session, user_id=USER_ID)
        self.repo.delete_user_from_care_plan_log.assert_called_with(
            session=session, user_id=USER_ID
        )
        self.repo.delete_user_from_patient.assert_called_with(
            session=session, user_id=USER_ID
        )

    def test__append_rag_threshold(self):
        class MockUser(MagicMock):
            recentModuleResults = {
                "5f1824ba504787d8d89ebeca": [
                    {
                        "Weight": {
                            "id": "5ff4b14e0b3791bf7278d9c6",
                            "userId": {"$oid": "5e8f0c74b50aa9656c34789b"},
                            "moduleId": "Weight",
                            "moduleConfigId": "5f1824ba504787d8d89ebeca",
                            "deploymentId": {"$oid": "5d386cc6ff885918d96edb2c"},
                            "version": 0,
                            "deviceName": "iOS",
                            "isAggregated": False,
                            "startDateTime": {"$date": "2021-01-05T18:34:54.000Z"},
                            "createDateTime": {"$date": "2021-01-05T18:34:54.658Z"},
                            "submitterId": {"$oid": "5f914cb28ee0158d37d2cf9c"},
                            "value": 1000,
                        }
                    }
                ]
            }

        user = MockUser()
        self.service._append_rag_threshold(user, {})

    @patch(f"{AUTH_PATH}.AuthorizationService._get_latest_observation_note_datetime")
    def test__append_recent_results_status(
        self, mock_get_latest_observation_note_datetime
    ):
        class MockUser(MagicMock):
            recentModuleResults = {}

        user = MockUser()
        mock_get_latest_observation_note_datetime.return_value = None
        self.service._append_recent_results_status(user)
        mock_get_latest_observation_note_datetime.assert_called_once()

    def test__get_latest_observation_note_datetime(self):
        class MockUser(MagicMock):
            recentModuleResults = {}

        self.service._deployment_service.retrieve_user_observation_notes.return_value = (
            None,
            0,
        )
        user = MockUser()
        self.assertIsNone(self.service._get_latest_observation_note_datetime(user))

    def test__add_badges(self):
        class MockUser(MagicMock):
            id = USER_ID
            set_field_value = MagicMock()

        user = MockUser()
        self.event_bus.emit = MagicMock(return_value=None)
        self.service._add_badges(user)
        event = GetUserBadgesEvent(user.id)
        self.event_bus.emit.assert_called_with(event)

        badges = [{"messages": 10}, {"appointments": 33}, {"downloads": 33}]
        self.event_bus.emit = MagicMock(return_value=badges)
        self.service._add_badges(user)
        event = GetUserBadgesEvent(user.id)
        user.set_field_value.assert_called_with(
            User.BADGES, reduce(lambda a, b: {**a, **b}, badges)
        )
        self.event_bus.emit.assert_called_with(event)

    @patch(f"{AUTH_PATH}.PostCreateAuthorizationBatchEvent")
    def test_update_covid_risk_score_just_return(self, post_create_auth_event):
        class MockUser(MagicMock):
            height = None
            biologicalSex = None
            dateOfBirth = None

        user = MockUser()
        deployment_id = "5ff5b1059ba9a480d78481ab"
        self.service.update_covid_risk_score(user, deployment_id)
        post_create_auth_event.assert_not_called()
        self.event_bus.emit.assert_not_called()
