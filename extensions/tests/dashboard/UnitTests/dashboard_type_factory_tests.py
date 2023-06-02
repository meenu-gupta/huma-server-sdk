import unittest

from extensions.dashboard.dashboard_types.dashboard_type_factory import (
    generate_dashboard_template_by_type,
)
from extensions.dashboard.dashboard_types.org_overview_type import (
    OrganizationOverviewType,
)
from extensions.dashboard.localization.localization_keys import (
    DashboardLocalizationKeys,
)
from extensions.dashboard.models.dashboard import DashboardId, Dashboard


class DashboardTypeFactoryTestCase(unittest.TestCase):
    def test_get_org_overview_type(self):
        org_name = "org name"
        res = generate_dashboard_template_by_type(
            DashboardId.ORGANIZATION_OVERVIEW.value, org_name
        )
        expected_res = {
            Dashboard.ID: DashboardId.ORGANIZATION_OVERVIEW.value,
            Dashboard.NAME: f"{DashboardLocalizationKeys.TITLE.value} {org_name}",
            Dashboard.GADGETS: OrganizationOverviewType().gadgets,
        }
        self.assertEqual(expected_res, res)

    def test_unexisting_dashboard_type(self):
        with self.assertRaises(NotImplementedError):
            generate_dashboard_template_by_type("something", "org_name")


if __name__ == "__main__":
    unittest.main()
