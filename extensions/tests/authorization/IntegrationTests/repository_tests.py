from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.tests.authorization.IntegrationTests.abstract_permission_test_case import (
    AbstractPermissionTestCase,
)
from sdk.common.utils import inject

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"


class BaseRepositoryTestCase(AbstractPermissionTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(BaseRepositoryTestCase, cls).setUpClass()
        cls.repo = inject.instance(AuthorizationRepository)


class AuthorizationRepositoryTestCase(BaseRepositoryTestCase):
    def test_retrieve_users_timezones(self):
        result = self.repo.retrieve_users_timezones()

        # check if the key type is ObjectId and value type is str.
        for key in result.keys():
            self.assertEqual(True, isinstance(key, str))
        for value in result.values():
            self.assertEqual(True, isinstance(value, str))

    def test_retrieve_simple_user_profile(self):
        user = self.repo.retrieve_simple_user_profile(user_id=VALID_USER_ID)
        self.assertIsNone(user.recentModuleResults)
        self.assertIsNone(user.tags)
        self.assertIsNone(user.tagsAuthorId)
