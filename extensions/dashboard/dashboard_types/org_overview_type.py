from extensions.dashboard.dashboard_types.base_dashboard_type import DashboardType
from extensions.dashboard.localization.localization_keys import (
    DashboardLocalizationKeys,
)
from extensions.dashboard.models.dashboard import Dashboard, DashboardId
from extensions.dashboard.models.gadget import GadgetId, GadgetLink


class OrganizationOverviewType(DashboardType):
    dashboard_id = DashboardId.ORGANIZATION_OVERVIEW.value

    def generate_template(self, resource_name: str) -> dict:
        return {
            Dashboard.ID: self.dashboard_id,
            Dashboard.NAME: f"{DashboardLocalizationKeys.TITLE.value} {resource_name}",
            Dashboard.GADGETS: self.gadgets,
        }

    @property
    def gadgets(self):
        return [
            {
                GadgetLink.SIZE: "2x2",
                GadgetLink.ORDER: 1,
                GadgetLink.ID: GadgetId.SIGNED_UP.value,
            },
            {
                GadgetLink.SIZE: "2x2",
                GadgetLink.ORDER: 2,
                GadgetLink.ID: GadgetId.CONSENTED.value,
            },
            {
                GadgetLink.SIZE: "2x2",
                GadgetLink.ORDER: 3,
                GadgetLink.ID: GadgetId.KEY_METRICS.value,
            },
            {
                GadgetLink.SIZE: "2x2",
                GadgetLink.ORDER: 4,
                GadgetLink.ID: GadgetId.OVERALL_VIEW.value,
            },
        ]
