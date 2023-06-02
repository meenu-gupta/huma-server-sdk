from extensions.dashboard.dashboard_types.dashboard_type_factory import DASHBOARD_TYPES
from extensions.dashboard.router.dashboard_requests import (
    RetrieveDashboardsRequestObject,
)
from extensions.dashboard.use_case.base_dashboard_use_case import BaseDashboardUseCase
from sdk.common.usecase.response_object import Response


class RetrieveDashboardsUseCase(BaseDashboardUseCase):
    def process_request(self, request_object: RetrieveDashboardsRequestObject):
        resource = self._get_resource(request_object)
        dashboards = [t().generate_template(resource.name) for t in DASHBOARD_TYPES]
        return Response(value=dashboards)
