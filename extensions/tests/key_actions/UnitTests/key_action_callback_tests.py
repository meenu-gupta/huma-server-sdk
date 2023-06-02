import unittest
from unittest.mock import MagicMock, patch

import pytz
from freezegun import freeze_time

from extensions.authorization.di.components import PostCreateUserEvent
from extensions.authorization.events.post_user_profile_update_event import (
    PostUserProfileUpdateEvent,
)
from extensions.authorization.models.user import User
from extensions.deployment.events import (
    PostCreateKeyActionConfigEvent,
    PostUpdateKeyActionConfigEvent,
    PostDeleteKeyActionConfigEvent,
)
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.key_action.callbacks.key_action_callback import (
    on_user_delete_callback,
    create_log_callback,
    create_key_actions_events,
    create_key_action_config_callback,
    create_surgery_key_action_on_user_change,
    update_key_actions_on_care_plan_group_change,
    update_key_actions_events,
    delete_key_action_config_callback,
)
from extensions.key_action.models.key_action_log import KeyAction
from extensions.module_result.event_bus.post_create_primitive import (
    PostCreatePrimitiveEvent,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.common.constants import VALUE_IN

SAMPLE_ID = "600a8476a961574fb38157d5"
CALLBACK_PATH = "extensions.key_action.callbacks.key_action_callback"


class KeyActionCallbackTestCase(unittest.TestCase):
    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_success_on_user_delete_callback(self, calendar_service):
        session = MagicMock()
        event = DeleteUserEvent(session=session, user_id=SAMPLE_ID)
        on_user_delete_callback(event)
        calendar_service().delete_user_events.assert_called_once_with(
            session=session, user_id=SAMPLE_ID
        )

    @freeze_time("2012-01-01")
    @patch(f"{CALLBACK_PATH}.get_dt_from_str")
    @patch(f"{CALLBACK_PATH}.CalendarService")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    def test_success_create_log_callback(
        self, auth_service, calendar_service, dt_from_str
    ):
        event = PostCreatePrimitiveEvent(
            module_config_id=SAMPLE_ID,
            module_id=SAMPLE_ID,
            module_result_id=SAMPLE_ID,
            user_id=SAMPLE_ID,
            primitive_name="some_name",
            deployment_id=SAMPLE_ID,
            device_name="some_device_name",
            id=SAMPLE_ID,
            create_date_time="2012-01-01T00:00:00Z",
        )
        tz = "UTC"
        auth_service().retrieve_simple_user_profile.return_value = User(timezone=tz)
        create_log_callback(event)
        auth_service().retrieve_simple_user_profile.assert_called_once_with(
            event.user_id
        )
        dt_from_str.assert_called_once_with(event.create_date_time)
        extra_options = {
            f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_ID}": event.module_id,
            f"{KeyAction.EXTRA_FIELDS}.{KeyAction.MODULE_CONFIG_ID}": event.module_config_id,
        }
        calendar_service().retrieve_calendar_events.assert_called_once_with(
            dt_from_str(),
            pytz.timezone(tz),
            model={VALUE_IN: [KeyAction.__name__, ScheduledEvent.__name__]},
            userId=SAMPLE_ID,
            **extra_options,
        )

    @patch(f"{CALLBACK_PATH}.CalendarService")
    def test_success_delete_key_action_config_callback(self, calendar_service):
        event = PostDeleteKeyActionConfigEvent(id=SAMPLE_ID)
        delete_key_action_config_callback(event)

        calendar_service().batch_delete_calendar_events.assert_called_with(
            {f"{KeyAction.EXTRA_FIELDS}.{KeyAction.KEY_ACTION_CONFIG_ID}": event.id}
        )

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_id")
    @patch(f"{CALLBACK_PATH}.KeyActionConfig")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.CalendarService")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_update_key_actions_events(
        self,
        deployment_service,
        calendar_service,
        auth_service,
        key_action_config,
        key_action_config_filter_by_id,
    ):
        event = PostUpdateKeyActionConfigEvent(
            deployment_id=SAMPLE_ID, key_action_config_id=SAMPLE_ID
        )

        key_action_config.id = SAMPLE_ID
        key_action_config_filter_by_id.return_value = iter(
            [key_action_config, key_action_config]
        )

        update_key_actions_events(event)

        retrieve_deployment_method = deployment_service().retrieve_deployment
        retrieve_deployment_method.assert_called_with(event.deployment_id)
        auth_service().retrieve_user_profiles_by_ids.assert_called_once()
        calendar_service().retrieve_raw_events.assert_called_with(
            **{
                f"{KeyAction.EXTRA_FIELDS}.{KeyAction.KEY_ACTION_CONFIG_ID}": key_action_config_filter_by_id()
                .__next__()
                .id
            }
        )

    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.CalendarService")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_update_key_actions_on_care_plan_group_change(
        self, deployment_service, calendar_service, auth_service, authz_user
    ):
        user = User(id=SAMPLE_ID, carePlanGroupId=SAMPLE_ID)
        event = PostUserProfileUpdateEvent(user)
        update_key_actions_on_care_plan_group_change(event)

        retrieve_profile_method = auth_service().retrieve_user_profile
        retrieve_profile_method.assert_called_with(user_id=user.id)
        authz_user.assert_called_with(retrieve_profile_method())
        deployment_service().retrieve_deployment_config.assert_called_with(authz_user())
        calendar_service().batch_delete_calendar_events("")

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_trigger")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_create_surgery_key_action_on_user_change(
        self,
        deployment_service,
        auth_service,
        authz_user,
        key_action_config_filter_by_trigger,
    ):
        user = User(id=SAMPLE_ID, surgeryDateTime="2012-01-01")
        event = PostUserProfileUpdateEvent(user)
        create_surgery_key_action_on_user_change(event)

        retrieve_profile_method = auth_service().retrieve_user_profile
        retrieve_profile_method.assert_called_with(user.id)
        retrieve_deployment_config_method = (
            deployment_service().retrieve_deployment_config
        )
        retrieve_deployment_config_method.assert_called_with(authz_user())
        key_action_config_filter_by_trigger.assert_called_with(
            retrieve_deployment_config_method().keyActions,
            KeyActionConfig.Trigger.SURGERY,
        )

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_trigger")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_create_surgery_key_action_not_called_no_surgery_date(
        self, deployment_service, auth_service, key_action_config_filter_by_trigger
    ):
        user = User(id=SAMPLE_ID)
        event = PostUserProfileUpdateEvent(user)
        create_surgery_key_action_on_user_change(event)

        auth_service().retrieve_user_profile.assert_not_called()
        deployment_service().retrieve_deployment_config.assert_not_called()
        key_action_config_filter_by_trigger.assert_not_called()

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_trigger")
    @patch(f"{CALLBACK_PATH}.AuthorizationService")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_create_surgery_key_action_not_called_surgery_date_not_updated(
        self, deployment_service, auth_service, key_action_config_filter_by_trigger
    ):
        user = User(id=SAMPLE_ID, surgeryDateTime="2021-01-01")
        event = PostUserProfileUpdateEvent(user, previous_state=user)
        create_surgery_key_action_on_user_change(event)

        auth_service().retrieve_user_profile.assert_not_called()
        deployment_service().retrieve_deployment_config.assert_not_called()
        key_action_config_filter_by_trigger.assert_not_called()

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_trigger")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    def test_success_create_surgery_key_action_called_surgery_date_updated_with_previous_state(
        self, dep_svc, mock_user, key_action_config_filter_by_trigger
    ):
        mock_user().is_user.return_value = True
        user = User(id=SAMPLE_ID, surgeryDateTime="2021-01-01")
        event = PostUserProfileUpdateEvent(
            user, previous_state=User(surgeryDateTime="2021-01-02")
        )
        dep_svc().retrieve_deployment_config.return_value = Deployment(
            keyActionsEnabled=True
        )
        create_surgery_key_action_on_user_change(event)

        key_action_config_filter_by_trigger.assert_called_once()

    @patch(f"{CALLBACK_PATH}.KeyActionGenerator", MagicMock())
    @patch(f"{CALLBACK_PATH}.CalendarService", MagicMock())
    @patch(f"{CALLBACK_PATH}.RetrieveProfilesRequestObject")
    @patch(f"{CALLBACK_PATH}.RetrieveProfilesUseCase")
    def test_success_create_key_action_config_callback(
        self, retrieve_profile_use_case, retrieve_profile_request_obj
    ):
        event = PostCreateKeyActionConfigEvent(
            deployment_id=SAMPLE_ID, key_action_config_id=SAMPLE_ID
        )
        create_key_action_config_callback(event)
        retrieve_profile_request_obj.assert_called_with(
            clean=True, deploymentId=event.deployment_id
        )
        retrieve_profile_use_case().execute.assert_called_with(
            retrieve_profile_request_obj()
        )

    @patch(f"{CALLBACK_PATH}.key_action_config_filter_by_trigger")
    @patch(f"{CALLBACK_PATH}.CalendarService", MagicMock())
    @patch(f"{CALLBACK_PATH}.DeploymentService")
    @patch(f"{CALLBACK_PATH}.AuthorizedUser")
    def test_success_create_key_actions_events(
        self, authz_user, deployment_service, key_action_config_filter_by_trigger
    ):
        user = User(id=SAMPLE_ID)
        event = PostCreateUserEvent(user=user)
        create_key_actions_events(event)
        authz_user.assert_called_with(user)

        retrieve_deployment_config = deployment_service().retrieve_deployment_config
        retrieve_deployment_config.assert_called_with(authz_user())
        key_action_config_filter_by_trigger.assert_called_with(
            retrieve_deployment_config().keyActions, KeyActionConfig.Trigger.SIGN_UP
        )


if __name__ == "__main__":
    unittest.main()
