from extensions.dashboard.dashboard_types.org_overview_type import (
    OrganizationOverviewType,
)

DASHBOARD_TYPES = (OrganizationOverviewType,)


def generate_dashboard_template_by_type(
    dashboard_type_name: str, resource_name: str
) -> dict:
    for dashboard_type in DASHBOARD_TYPES:
        if dashboard_type_name == dashboard_type.dashboard_id:
            return dashboard_type().generate_template(resource_name)
    raise NotImplementedError(f"No dashboard with type {dashboard_type_name}")
