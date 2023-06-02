import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.tests.authorization.UnitTests.user_fields_converter_tests import (
    DEPLOYMENT_ID,
)
from sdk.common.localization.utils import Language, Localization
from sdk.common.utils import inject

AUTH_MODEL_PATH = "extensions.authorization.models.authorized_user"


class AuthModelTestCase(TestCase):
    def setUp(self) -> None:
        self.deployment_repo = MagicMock()

        def bind(binder):
            binder.bind(DeploymentRepository, self.deployment_repo)
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(bind)

    @staticmethod
    def _sample_role_assignment(resource: str) -> RoleAssignment:
        return RoleAssignment.from_dict(
            {
                RoleAssignment.ROLE_ID: RoleName.USER,
                RoleAssignment.RESOURCE: resource,
            }
        )

    def test_success_get_role_by_resource(self):
        user = User(
            roles=[self._sample_role_assignment("deployment/6156ad33a7082b29f6c6d0e8")]
        )
        user.roles[0].resource = None
        auth_user = AuthorizedUser(user=user)
        try:
            auth_user._get_role_by_resource("resource")
        except TypeError:
            self.fail()

    def test_retrieve_organization_ids__star_resource_is_filtered(self):
        org_id = "6156ad33a7082b29f6c6d0e8"
        user = User(
            roles=[
                self._sample_role_assignment("organization/*"),
                self._sample_role_assignment(f"organization/{org_id}"),
            ]
        )
        auth_user = AuthorizedUser(user=user)
        res = auth_user.organization_ids()
        self.assertIn(org_id, res)
        self.assertNotIn("*", res)
        self.assertEqual(1, len(res))

    @patch(
        "extensions.authorization.models.authorized_user.AuthorizedUser.deployment_id"
    )
    @patch("extensions.authorization.models.authorized_user.AuthorizedUser.deployment")
    def test_user_localization(self, deployment, mocked_deployment_id):
        user = User(language=Language.EN)
        deployment.get_localization.return_value = {
            "deployment_translation_key": "deployment translation value"
        }
        mocked_deployment_id.return_value = DEPLOYMENT_ID
        auth_user = AuthorizedUser(user=user)
        res = auth_user.localization
        expected_res = {
            "deployment_translation_key": "deployment translation value",
        }
        self.assertEqual(
            expected_res["deployment_translation_key"],
            res["deployment_translation_key"],
        )

    def test_authorized_user_str(self):
        user = User(
            roles=[
                self._sample_role_assignment("organization/123"),
            ]
        )
        auth_user = AuthorizedUser(user=user)
        self.assertEqual(
            f"{auth_user}",
            (
                f"[{AuthorizedUser.__name__} {AuthorizedUser.DEPLOYMENT_ID}: {auth_user._deployment_id}, "
                f"{AuthorizedUser.ORGANIZATION_ID}: {auth_user._organization_id}, "
                f"{AuthorizedUser.ROLE}: {auth_user._role.id}, "
                f"{AuthorizedUser.ROLE_ASSIGNMENT}: {auth_user._role_assignment}]"
            ),
        )

    def _retrieve_expected_json(self, config_name: str):
        module_path = f"{Path(__file__).parents[4]}/extensions/module_result/modules/licensed_configs/{config_name}.json"
        with open(module_path) as file:
            return json.load(file)
