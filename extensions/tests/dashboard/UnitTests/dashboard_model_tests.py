import unittest

from extensions.dashboard.models.dashboard import (
    Dashboard,
    GadgetLink,
    DashboardId,
)
from extensions.dashboard.models.gadget import GadgetId
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "6284a61b0fdb62fd01bb3ef0"


class DashboardModelTestCase(unittest.TestCase):
    def test_success_create_gadget(self):
        try:
            Dashboard.from_dict(self._sample_dashboard_dict())
        except ConvertibleClassValidationError:
            self.fail()

    @staticmethod
    def _sample_dashboard_dict():
        return {
            Dashboard.NAME: "some name",
            Dashboard.ID: DashboardId.ORGANIZATION_OVERVIEW.value,
            Dashboard.GADGETS: [
                {
                    GadgetLink.SIZE: "2x2",
                    GadgetLink.ORDER: 1,
                    GadgetLink.ID: GadgetId.SIGNED_UP.value,
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
