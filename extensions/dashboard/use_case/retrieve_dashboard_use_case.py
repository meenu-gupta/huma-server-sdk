from extensions.dashboard.dashboard_types.dashboard_type_factory import (
    generate_dashboard_template_by_type,
)
from extensions.dashboard.router.dashboard_requests import (
    RetrieveDashboardRequestObject,
)
from extensions.dashboard.use_case.base_dashboard_use_case import BaseDashboardUseCase
from sdk.common.usecase.response_object import Response


class RetrieveDashboardUseCase(BaseDashboardUseCase):
    def process_request(self, request_object: RetrieveDashboardRequestObject):
        resource = self._get_resource(request_object)
        dashboard = generate_dashboard_template_by_type(
            request_object.dashboardId.value, resource.name
        )
        return Response(value=dashboard)
