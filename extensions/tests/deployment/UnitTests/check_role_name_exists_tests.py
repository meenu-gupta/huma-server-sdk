from unittest import TestCase

from extensions.authorization.models.role.role import Role
from extensions.deployment.models.deployment import Deployment


class CheckRoleNameAlreadyExistsTests(TestCase):
    def setUp(self):
        self.role_name = "Nurse"
        self.deployment = Deployment(
            roles=[
                Role.from_dict(
                    {
                        Role.NAME: self.role_name,
                        Role.PERMISSIONS: ["VIEW_PATIENT_DATA", "MANAGE_PATIENT_DATA"],
                    }
                ),
                Role.from_dict(
                    {Role.NAME: "Readonly", Role.PERMISSIONS: ["VIEW_PATIENT_DATA"]}
                ),
            ]
        )

    def test_when_role_name_already_exists(self):
        self.assertTrue(self.deployment.role_name_exists(self.role_name))

    def test_when_role_name_does_not_exist(self):
        self.assertFalse(self.deployment.role_name_exists(self.role_name + "a"))
