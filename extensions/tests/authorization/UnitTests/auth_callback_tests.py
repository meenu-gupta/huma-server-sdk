import unittest
from unittest.mock import patch, MagicMock

from flask import Flask, request
from freezegun import freeze_time

from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from extensions.authorization.callbacks import (
    get_file_name_from_request,
    on_token_extraction_callback,
    validate_filename,
    allow_ip_callback,
    extract_user,
    on_user_delete_callback,
    check_deployment_mfa,
    delete_user_role,
    update_user_profile_email,
    update_calendar_on_profile_update,
    update_recent_module_results,
    create_tag_log,
    mark_auth_user_email_verified,
    get_default_care_plan_group,
    are_client_permissions_valid,
    check_set_auth_attributes,
    on_calendar_view_users_data_callback,
    register_user_with_role,
    check_valid_client_used,
    send_user_reactivation_email,
    send_user_off_board_notifications,
    update_user_profile_last_login,
)
from extensions.authorization.callbacks.callbacks import create_assign_label_logs
from extensions.authorization.events.post_assign_label_event import PostAssignLabelEvent
from extensions.authorization.events.post_create_tag_event import PostCreateTagEvent
from extensions.authorization.events.post_user_off_board_event import (
    PostUserOffBoardEvent,
)
from extensions.authorization.events.post_user_profile_update_event import (
    PostUserProfileUpdateEvent,
)
from extensions.authorization.events.post_user_reactivation_event import (
    PostUserReactivationEvent,
)
from extensions.authorization.models.label_log import LabelLog
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.tag_log import TagLog
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.events.delete_custom_roles_event import (
    DeleteDeploymentCustomRolesEvent,
)
from extensions.deployment.models.care_plan_group.care_plan_group import CarePlanGroup
from extensions.deployment.models.deployment import Deployment, Label
from extensions.module_result.event_bus.post_create_module_results_batch_event import (
    PostCreateModuleResultBatchEvent,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_sample_labels,
)
from extensions.tests.shared.test_helpers import get_server_project
from sdk.auth.decorators import check_token_valid_for_mfa
from sdk.auth.enums import Method, AuthStage
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.auth.events.post_sign_in_event import PostSignInEvent
from sdk.auth.events.post_sign_up_event import PostSignUpEvent
from sdk.auth.events.set_auth_attributes_events import (
    PostSetAuthAttributesEvent,
    PreSetAuthAttributesEvent,
    PreRequestPasswordResetEvent,
)
from sdk.auth.events.token_extraction_event import TokenExtractionEvent
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.calendar.events import CalendarViewUserDataEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    DetailedException,
    MFARequiredException,
    ClientPermissionDenied,
    AccessTokenNotValidForMultiFactorAuthException,
)
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import USER_CLAIMS_KEY, AUTH_STAGE
from sdk.phoenix.config.server_config import Client, PhoenixServerConfig
from sdk.tests.auth.test_helpers import (
    USER_ID,
    USER_EMAIL,
    PROJECT_ID,
    TEST_CLIENT_ID,
    CLIENT_ID_3,
)

SAMPLE_ID = "600a8476a961574fb38157d5"
CALLBACK_PATH = "extensions.authorization.callbacks.callbacks"

testapp = Flask(__name__)


class CallbackTestCase(unittest.TestCase):
    def test_success_get_file_name_from_request(self):
        file_name = "aaa/bbb/ccc"
        with testapp.test_request_context("/", method="POST") as _:
            request.form = {"filename": file_name}
            res = get_file_name_from_request()
            self.assertEqual(res, file_name)

    def test_failure_get_file_name_from_request(self):
        with testapp.test_request_context("/", method="POST") as _:
            with self.assertRaises(InvalidRequestException):
                get_file_name_from_request()

    @patch(f"{CALLBACK_PATH}.AuthorizationMiddleware")
    def test_success_on_token_extraction_callback(self, auth_middleware):
        email = "dummy@mail.com"
        event = TokenExtractionEvent(id=SAMPLE_ID, email=email)
        with testapp.test_request_context("/") as _:
            on_token_extraction_callback(event)
            auth_middleware(request).assert_called_with(SAMPLE_ID)

    def test_success_validate_filename(self):
        try:
            file_name = "aaa/bbb/ccc"
            validate_filename(file_name)
        except InvalidRequestException:
            self.fail()

    @patch("sdk.common.utils.inject.get_injector_or_die", MagicMock())
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.PreSignUpEvent")
    def test_success_allow_ip_callback(self, pre_sign_up_event, auth_service):
        auth_service.check_ip_allowed_create_super_admin = True
        pre_sign_up_event.validation_data = {"masterKey": "test_key"}
        try:
            allow_ip_callback(pre_sign_up_event)
        except DetailedException:
            self.fail()

    @patch("sdk.common.utils.inject.get_injector_or_die", MagicMock())
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_extract_user(self, auth_service):
        user_id = SAMPLE_ID
        auth_service.retrieve_user_profile.return_value = {}

        with testapp.test_request_context("/") as _:
            extract_user(user_id)
            auth_service().retrieve_user_profile.assert_called_with(SAMPLE_ID)

    @patch("sdk.common.utils.inject.get_injector_or_die", MagicMock())
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_on_user_delete_callback(self, auth_service):
        auth_service.delete_user.return_value = MagicMock()
        session = MagicMock()
        event = DeleteUserEvent(user_id=SAMPLE_ID, session=session)
        on_user_delete_callback(event)
        auth_service.assert_called_with()
        auth_service().delete_user.assert_called_once_with(
            session=session, user_id=SAMPLE_ID
        )

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.verify_jwt_in_request")
    @patch(f"{CALLBACK_PATH}.check_token_valid_for_mfa")
    def test_success_check_deployment_mfa(
        self, token_check, verify_jwt_mock, _, auth_service
    ):
        event = TokenExtractionEvent(id=SAMPLE_ID, phone_number=1212)
        check_deployment_mfa(event)
        verify_jwt_mock.assert_called_once_with()
        token_check.assert_called_once_with(verify_jwt_mock())
        auth_service().retrieve_user_profile.assert_called_once_with(SAMPLE_ID)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_delete_user_role(self, _):
        event = DeleteDeploymentCustomRolesEvent(
            deleted_ids=[SAMPLE_ID], deployment_id=SAMPLE_ID
        )
        mock_repo = MagicMock()()
        mock_repo.retrieve_user_profiles.return_value = [], None
        delete_user_role(event, mock_repo)
        mock_repo.retrieve_user_profiles.assert_called_once_with(
            deployment_id=SAMPLE_ID, search="", role=RoleName.MANAGER
        )

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.extract_user")
    @patch(f"{CALLBACK_PATH}.UpdateUserProfileRequestObject")
    def test_success_update_user_profile_email(
        self, update_profile_req_obj, extract_user_mock, auth_service
    ):
        event = PostSetAuthAttributesEvent(
            user_id=SAMPLE_ID, email="new_dummy_email@mail.com"
        )
        extract_user_mock.return_value = User()
        update_user_profile_email(event)
        auth_service().update_user_profile.assert_called_once_with(
            update_profile_req_obj()
        )

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.UpdateUserProfileRequestObject")
    def test_success_update_user_profile_last_login(
        self, update_profile_req_obj, auth_service
    ):
        event = PostSignInEvent(user_id=SAMPLE_ID)
        update_user_profile_last_login(event)
        auth_service().update_user_profile.assert_called_once_with(
            update_profile_req_obj()
        )

    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_success_update_calendar_on_profile_update(self, calendar_service):
        timezone = "UTC"
        user = User(timezone=timezone, id=SAMPLE_ID)
        event = PostUserProfileUpdateEvent(user)
        update_calendar_on_profile_update(event=event)
        calendar_service().calculate_and_save_next_day_events_for_user.assert_called_once_with(
            SAMPLE_ID, timezone
        )

    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_calendar_not_updated_on_profile_update_no_timezone(self, calendar_service):
        user = User(id=SAMPLE_ID, givenName="TestUser")
        event = PostUserProfileUpdateEvent(user)
        update_calendar_on_profile_update(event=event)
        calendar_service().calculate_and_save_next_day_events_for_user.assert_not_called()

    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_calendar_not_updated_on_profile_update_same_timezone(
        self, calendar_service
    ):
        timezone = "Europe/Kiev"
        user = User(id=SAMPLE_ID, timezone=timezone)
        previous_state = User(id=SAMPLE_ID, timezone=timezone, givenName="User")
        event = PostUserProfileUpdateEvent(user, previous_state)
        update_calendar_on_profile_update(event=event)
        calendar_service().calculate_and_save_next_day_events_for_user.assert_not_called()

    @freeze_time("2012-01-01")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_update_recent_module_results(self, auth_service):
        event = PostCreateModuleResultBatchEvent(
            primitives={},
            deployment_id=SAMPLE_ID,
            user_id=SAMPLE_ID,
            module_id=SAMPLE_ID,
            module_result_id=SAMPLE_ID,
            module_config_id=SAMPLE_ID,
            device_name="dummy device",
            start_date_time="2012-01-01",
        )
        update_recent_module_results(event)
        auth_service().update_recent_results.assert_called_once_with([])

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_create_tag_log(self, auth_service):
        tags = {}
        event = PostCreateTagEvent(user_id=SAMPLE_ID, author_id=SAMPLE_ID, tags=tags)
        create_tag_log(event)
        tag_log = TagLog(
            id=None, userId=SAMPLE_ID, authorId=SAMPLE_ID, tags={}, createDateTime=None
        )
        auth_service().create_tag_log.assert_called_once_with(tag_log)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_create_assign_label_log(self, auth_service):
        labels: list[Label] = [
            Label.from_dict(label_dict) for label_dict in get_sample_labels()
        ]
        event = PostAssignLabelEvent(
            user_ids=[SAMPLE_ID], assignee_id=SAMPLE_ID, labels=labels
        )
        create_assign_label_logs(event)
        label_logs = [
            LabelLog(
                id=None,
                userId=SAMPLE_ID,
                assigneeId=SAMPLE_ID,
                labelId=label.id,
                createDateTime=None,
            )
            for label in labels
        ]
        auth_service().create_assign_label_logs.assert_called_once_with(label_logs)

    @patch(f"{CALLBACK_PATH}.AuthRepository")
    def test_success_mark_auth_user_email_verified(self, auth_repo):
        session = MagicMock()
        test_email = "dummy_test_email@mail.com"
        user = User(id=SAMPLE_ID, email=test_email)
        mark_auth_user_email_verified(session=session, user=user, auth_repo=auth_repo)
        self.assertEqual(auth_repo.session, session)
        auth_repo.confirm_email.assert_called_once_with(uid=SAMPLE_ID, email=test_email)

    def test_success_get_default_care_plan_group(self):
        group_mock = MagicMock()
        careplan_group = CarePlanGroup(groups=[group_mock])
        deployment = Deployment(carePlanGroup=careplan_group)
        res = get_default_care_plan_group(deployment=deployment)
        self.assertEqual(res, group_mock)

    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_success_are_client_permissions_valid(self, authz_user):
        client = Client(roleIds=[SAMPLE_ID])
        authz_user.user_type.return_value = SAMPLE_ID
        res = are_client_permissions_valid(client=client, user=authz_user)
        self.assertTrue(res)

    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_check_set_auth_attributes(self, auth_service, authz_user):
        event = PreSetAuthAttributesEvent(user_id=SAMPLE_ID, mfa_enabled=False)
        with self.assertRaises(MFARequiredException):
            check_set_auth_attributes(event)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_on_calendar_view_users_data_callback(self, auth_service):
        event = CalendarViewUserDataEvent()
        on_calendar_view_users_data_callback(event)
        required_fields = ("createDateTime", "surgeryDateTime")
        auth_service().retrieve_users_with_user_role_including_only_fields.assert_called_once_with(
            required_fields, to_model=False
        )

    @patch(f"{CALLBACK_PATH}._prepare_new_user")
    @patch(f"{CALLBACK_PATH}.check_if_participant_off_boarded", MagicMock())
    @patch(f"{CALLBACK_PATH}.inject", MagicMock())
    @patch(f"{CALLBACK_PATH}.get_client", MagicMock())
    @patch(f"{CALLBACK_PATH}.are_client_permissions_valid", MagicMock())
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_register_user_with_role(
        self, auth_service, authz_user, new_user_mock
    ):
        email = "dummy@email.com"
        event = PostSignUpEvent(email=email)
        register_user_with_role(event)
        auth_service().create_user.assert_called_once_with(new_user_mock(), None)

    def test_check_valid_client_used__pre_request_password_event(self):
        auth_repo = MagicMock()

        config = MagicMock()
        config.server.project = get_server_project()

        def bind_and_configure(binder):
            binder.bind(AuthorizationRepository, auth_repo)
            binder.bind(PhoenixServerConfig, config)
            binder.bind(DefaultRoles, DefaultRoles())
            binder.bind(EventBusAdapter, EventBusAdapter())

        inject.clear_and_configure(bind_and_configure)
        role = RoleAssignment._create_role(RoleName.USER, f"deployment/{SAMPLE_ID}")
        auth_repo.retrieve_user.return_value = User(id=USER_ID, roles=[role])

        # Using User client and User role
        event = PreRequestPasswordResetEvent(
            user_id=USER_ID, client_id=TEST_CLIENT_ID, project_id=PROJECT_ID
        )
        check_valid_client_used(event)
        # Using Manager client and User role
        event = PreRequestPasswordResetEvent(
            user_id=USER_ID, client_id=CLIENT_ID_3, project_id=PROJECT_ID
        )
        with self.assertRaises(ClientPermissionDenied):
            check_valid_client_used(event)

    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_send_user_reactivation_email(self, mock_auth_svc):
        email_adapter = MagicMock()

        def bind_and_configure(binder):
            binder.bind(UserEmailAdapter, email_adapter)

        inject.clear_and_configure(bind_and_configure)
        event = PostUserReactivationEvent(user_id=SAMPLE_ID)
        send_user_reactivation_email(event)
        mock_auth_svc().retrieve_simple_user_profile.assert_called_with(
            user_id=event.user_id
        )
        email_adapter.send_reactivate_user_email.assert_called_once()

    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.prepare_and_send_push_notification")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_send_user_off_board_notifications_only_push(
        self, mock_auth_svc, mock_push, mock_auth_user
    ):
        email_adapter = MagicMock()

        def bind_and_configure(binder):
            binder.bind(UserEmailAdapter, email_adapter)

        inject.clear_and_configure(bind_and_configure)

        user = User(id=SAMPLE_ID)
        mock_auth_svc().retrieve_simple_user_profile.return_value = user

        event = PostUserOffBoardEvent(user_id=SAMPLE_ID, detail="Recovered")
        send_user_off_board_notifications(event)
        mock_auth_svc().retrieve_simple_user_profile.assert_called_with(
            user_id=event.user_id
        )
        mock_push.assert_called_once()
        mock_auth_user.assert_called_with(user)
        email_adapter.send_off_board_user_email.assert_not_called()

    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.prepare_and_send_push_notification")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_send_user_off_board_notifications(
        self, mock_auth_svc, mock_push, mock_auth_user
    ):
        email_adapter = MagicMock()

        def bind_and_configure(binder):
            binder.bind(UserEmailAdapter, email_adapter)

        inject.clear_and_configure(bind_and_configure)

        user = User(id=SAMPLE_ID, email=USER_EMAIL)
        mock_auth_svc().retrieve_simple_user_profile.return_value = user

        event = PostUserOffBoardEvent(user_id=SAMPLE_ID, detail="Recovered")
        send_user_off_board_notifications(event)
        mock_auth_svc().retrieve_simple_user_profile.assert_called_with(
            user_id=event.user_id
        )
        mock_push.assert_called_once()
        mock_auth_user.assert_called_with(user)
        email_adapter.send_off_board_user_email.assert_called_once()

    def test_check_token_valid_for_mfa__invalid_with_mfa_method(self):
        decoded_token = {
            USER_CLAIMS_KEY: {SignInRequestObject.METHOD: Method.TWO_FACTOR_AUTH}
        }
        with self.assertRaises(AccessTokenNotValidForMultiFactorAuthException):
            check_token_valid_for_mfa(decoded_token)

    def test_check_token_valid_for_mfa__invalid_with_first_stage(self):
        decoded_token = {USER_CLAIMS_KEY: {AUTH_STAGE: AuthStage.FIRST}}
        with self.assertRaises(AccessTokenNotValidForMultiFactorAuthException):
            check_token_valid_for_mfa(decoded_token)

    def test_check_token_valid_for_mfa__invalid_with_first_stage_int(self):
        decoded_token = {USER_CLAIMS_KEY: {AUTH_STAGE: 1}}
        with self.assertRaises(AccessTokenNotValidForMultiFactorAuthException):
            check_token_valid_for_mfa(decoded_token)

    def test_check_token_valid_for_mfa__invalid_with_normal_stage(self):
        decoded_token = {USER_CLAIMS_KEY: {AUTH_STAGE: AuthStage.NORMAL}}
        with self.assertRaises(AccessTokenNotValidForMultiFactorAuthException):
            check_token_valid_for_mfa(decoded_token)

    def test_check_token_valid_for_mfa__valid_with_second_stage(self):
        decoded_token = {USER_CLAIMS_KEY: {AUTH_STAGE: AuthStage.SECOND}}
        try:
            check_token_valid_for_mfa(decoded_token)
        except AccessTokenNotValidForMultiFactorAuthException:
            self.fail()

    def test_check_token_valid_for_mfa__valid_with_second_stage_int(self):
        decoded_token = {USER_CLAIMS_KEY: {AUTH_STAGE: 2}}
        try:
            check_token_valid_for_mfa(decoded_token)
        except AccessTokenNotValidForMultiFactorAuthException:
            self.fail()


if __name__ == "__main__":
    unittest.main()
