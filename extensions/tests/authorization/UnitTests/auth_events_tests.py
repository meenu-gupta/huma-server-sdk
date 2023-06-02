import unittest
from unittest.mock import MagicMock

from extensions.authorization.callbacks import check_valid_client_used
from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.events.post_create_authorization_event import (
    PostCreateAuthorizationEvent,
)
from extensions.authorization.events.pre_create_authorization_event import (
    PreCreateAuthorizationEvent,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.auth.events.set_auth_attributes_events import PreRequestPasswordResetEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig

SAMPLE_ID = "600a8476a961574fb38157d5"


class PostCreateAuthorizationEventTestCase(unittest.TestCase):
    def test_success_init_post_create_event(self):
        kwargs = {
            "id": SAMPLE_ID,
            "create_date_time": "2010/10/10",
            "module_id": SAMPLE_ID,
            "user_id": SAMPLE_ID,
            "deployment_id": SAMPLE_ID,
            "device_name": "device_name",
        }
        res = PostCreateAuthorizationEvent(**kwargs)
        self.assertIsNotNone(res)


class PreCreateAuthorizationEventTestCase(unittest.TestCase):
    def test_success_init_pre_create_event(self):
        kwargs = {
            "module_id": SAMPLE_ID,
            "user_id": SAMPLE_ID,
            "deployment_id": SAMPLE_ID,
            "device_name": "device_name",
        }
        res = PreCreateAuthorizationEvent(**kwargs)
        self.assertIsNotNone(res)


class EventBinderTestCase(unittest.TestCase):
    def test_pre_request_password_events_binded(self):
        adapter = EventBusAdapter()

        def bind_and_configure(binder):
            binder.bind(EventBusAdapter, adapter)
            binder.bind(PhoenixServerConfig, MagicMock())
            binder.bind(AuthorizationRepository, MagicMock())

        inject.clear_and_configure(bind_and_configure)
        auth_component = AuthorizationComponent()
        auth_component.config = MagicMock()
        auth_component.post_setup()
        self.assertIn(PreRequestPasswordResetEvent, adapter._handlers)
        callbacks = adapter._handlers.get(PreRequestPasswordResetEvent)
        self.assertIsNotNone(callbacks)
        self.assertIn(check_valid_client_used, callbacks)


if __name__ == "__main__":
    unittest.main()
