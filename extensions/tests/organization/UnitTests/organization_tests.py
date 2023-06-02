import unittest

from extensions.deployment.models.status import Status
from extensions.organization.models.organization import Organization


class OrganizationToDictTestCase(unittest.TestCase):
    def test_success_organization_to_dict(self):
        status = Status.DEPLOYED
        name = "Test Organization"
        organization = Organization(name=name, status=status)
        organization_dict = organization.to_dict()

        self.assertEqual(organization_dict["name"], name)
        self.assertEqual(organization_dict["status"], status.name)
