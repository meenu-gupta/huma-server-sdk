import unittest
from unittest.mock import patch, MagicMock

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.events import PostDeploymentUpdateEvent
from extensions.deployment.models.deployment import Deployment, Features
from extensions.module_result.callbacks.callbacks import (
    on_user_delete_callback,
    check_retrieve_permissions,
    disable_schedule_events,
)
from extensions.module_result.event_bus.post_retrieve_primitive import (
    PostRetrievePrimitiveEvent,
)
from extensions.module_result.models.scheduled_event import ScheduledEvent
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.common.utils import inject

SAMPLE_ID = "600a8476a961574fb38157d5"
CALLBACK_PATH = "extensions.module_result.callbacks.callbacks"


class ModuleResultCallbackTestCase(unittest.TestCase):
    auth_repo: MagicMock

    @classmethod
    def setUpClass(cls) -> None:
        cls.auth_repo = MagicMock()
        cls.auth_repo.retrieve_user_ids_in_deployment.return_value = [SAMPLE_ID]

        def bind(binder):
            binder.bind(AuthorizationRepository, cls.auth_repo)

        inject.clear_and_configure(bind)

    @patch(f"{CALLBACK_PATH}.ModuleResultService")
    def test_success_on_user_delete_callback(self, module_result_service):
        session = MagicMock()
        event = DeleteUserEvent(user_id=SAMPLE_ID, session=session)
        on_user_delete_callback(event)
        module_result_service().delete_user_primitive.assert_called_with(
            session=session, user_id=SAMPLE_ID
        )

    @patch(f"{CALLBACK_PATH}.check_proxy_permission")
    def test_success_check_retrieve_permissions(self, check_permission):
        event = PostRetrievePrimitiveEvent(
            deployment_id=SAMPLE_ID,
            device_name=SAMPLE_ID,
            module_id=SAMPLE_ID,
            module_result_id=SAMPLE_ID,
            primitive_name=SAMPLE_ID,
            user_id=SAMPLE_ID,
        )
        check_retrieve_permissions(event)
        check_permission.assert_called_with(SAMPLE_ID)

    def test_disable_schedule_events_flag_present(self):
        service = MagicMock()
        deployment = Deployment(features=Features())
        for flag in [True, False]:
            deployment.features.personalizedConfig = flag
            disable_schedule_events(deployment, service)
            filter_options = {
                ScheduledEvent.MODEL: ScheduledEvent.__name__,
                ScheduledEvent.USER_ID: [SAMPLE_ID],
            }
            service.update_events_status.assert_called_once_with(filter_options, flag)
            service.reset_mock()

    def test_disable_schedule_events_flag_missing(self):
        service = MagicMock()
        disable_schedule_events(Deployment(), service)
        service.update_events_status.assert_not_called()

        disable_schedule_events(
            Deployment(features=Features(personalizedConfig=None)), service
        )
        service.update_events_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
