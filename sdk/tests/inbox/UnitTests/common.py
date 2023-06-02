import unittest
from unittest.mock import MagicMock

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.inbox.repo.inbox_repository import InboxRepository

USER_ID_1 = "5e8f0c74b50aa9656c34789a"
USER_ID_2 = "5e84b0dab8dfa268b1180536"
MESSAGE_ID = "5e84b0dab8dfa268b1180540"
MOCK_PAYLOAD = {"a": "b"}


class BaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.event_bus = MagicMock()
        self.inbox_repo = MagicMock()
        self.auth_repo = MagicMock()

        def bind(binder):
            binder.bind(InboxRepository, self.inbox_repo)
            binder.bind(EventBusAdapter, self.event_bus)
            binder.bind(AuthorizationRepository, self.auth_repo)

        inject.clear_and_configure(bind)
