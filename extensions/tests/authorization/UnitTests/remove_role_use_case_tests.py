import unittest
from unittest.mock import MagicMock

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.router.user_profile_request import (
    RemoveRolesRequestObject,
)
from extensions.authorization.use_cases.remove_role_use_case import RemoveRolesUseCase
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.tests.authorization.UnitTests.update_roles_tests import get_authz_user
from sdk.common.utils import inject

SAMPLE_VALID_OBJ_ID = "60a20766c85cd55b38c99e12"
DEPLOYMENT_1_ID = "501919b5c03550c421c075aa"


class RemoveRoleUseCaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            binder.bind_to_provider(OrganizationRepository, lambda: MagicMock())

        inject.clear_and_configure(bind)

    def test_success_remove_role_use_case(self):
        auth_repo = MagicMock()
        deployment_repo = MagicMock()
        org_repo = MagicMock()
        use_case = RemoveRolesUseCase(
            repo=auth_repo, deployment_repo=deployment_repo, organization_repo=org_repo
        )
        user = self._sample_user()
        auth_repo.retrieve_simple_user_profile.return_value = user
        req_obj = RemoveRolesRequestObject.from_dict(
            {
                RemoveRolesRequestObject.USER_ID: user.id,
                RemoveRolesRequestObject.SUBMITTER: get_authz_user(
                    RoleName.ADMIN, DEPLOYMENT_1_ID
                ),
                RemoveRolesRequestObject.ROLES: [self._sample_role_assignment_dict()],
            }
        )
        use_case.execute(req_obj)
        user.roles = []
        user.email = None
        auth_repo.update_user_profile.assert_called_once_with(user)

    def _sample_user(self):
        return User.from_dict(
            {
                User.ID: SAMPLE_VALID_OBJ_ID,
                User.EMAIL: "test_user_email@huma.com",
                User.ROLES: [self._sample_role_assignment_dict()],
            }
        )

    @staticmethod
    def _sample_role_assignment_dict():
        return {
            RoleAssignment.ROLE_ID: RoleName.ACCESS_CONTROLLER,
            RoleAssignment.RESOURCE: "deployment/resource",
        }


if __name__ == "__main__":
    unittest.main()
