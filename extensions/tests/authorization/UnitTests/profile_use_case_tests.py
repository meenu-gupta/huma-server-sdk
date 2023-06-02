from unittest import TestCase
from unittest.mock import patch, MagicMock

from extensions.authorization.models.user import User
from extensions.authorization.router.user_profile_request import (
    RetrieveProfilesRequestObject,
    SortParameters,
)
from extensions.authorization.use_cases.retrieve_profiles_use_case import (
    RetrieveProfilesUseCase,
)
from extensions.module_result.modules import rag_enabled_module_ids
from sdk.common.utils import inject

CACHE_SERVICE_PATH = "extensions.authorization.use_cases.retrieve_profiles_use_case"


class RetrieveProfilesUseCaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        inject.clear_and_configure(lambda x: None)
        rag_enabled_module_ids.append("TestModule")

    @classmethod
    def tearDownClass(cls):
        rag_enabled_module_ids.remove("TestModule")

    def setUp(self) -> None:
        user1 = User(id="UserWithMoreSeverities")
        user1.ragThresholds = {
            "a": {"TestModule": {"severities": [3]}},
            "b": {"TestModule": {"severities": [1]}},
        }
        user2 = User(id="UserWithLessSeverities")
        user2.ragThresholds = {"a": {"TestModule": {"severities": [1]}}}
        self.users = [user1, user2]

    @patch(f"{CACHE_SERVICE_PATH}.CachingService", MagicMock())
    def test_descending_sort_by_rag(self):
        sort = SortParameters(
            fields=[SortParameters.Field.RAG], order=SortParameters.Order.DESCENDING
        )
        use_case = RetrieveProfilesUseCase(None, None, None)
        use_case.request_object = RetrieveProfilesRequestObject(sort=sort)
        users = use_case._sort_by_rag(self.users)
        self.assertEqual("UserWithMoreSeverities", users[0].id)

    @patch(f"{CACHE_SERVICE_PATH}.CachingService", MagicMock())
    def test_ascending_sort_by_rag(self):
        sort = SortParameters(
            fields=[SortParameters.Field.RAG], order=SortParameters.Order.ASCENDING
        )
        use_case = RetrieveProfilesUseCase(None, None, None)
        use_case.request_object = RetrieveProfilesRequestObject(sort=sort)
        users = use_case._sort_by_rag(self.users)
        self.assertEqual("UserWithLessSeverities", users[0].id)
