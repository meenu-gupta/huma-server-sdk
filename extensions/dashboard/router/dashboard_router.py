from flasgger import swag_from
from flask import jsonify, request, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.dashboard.router.dashboard_requests import (
    RetrieveDashboardsRequestObject,
    RetrieveDashboardRequestObject,
    RetrieveGadgetDataRequestObject,
)
from extensions.dashboard.use_case.retrieve_dashboard_use_case import (
    RetrieveDashboardUseCase,
)
from extensions.dashboard.use_case.retrieve_dashboards_use_case import (
    RetrieveDashboardsUseCase,
)
from extensions.dashboard.use_case.retrieve_gadget_data_use_case import (
    RetrieveGadgetDataUseCase,
)
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.json_utils import replace_values

RESOURCE_TYPE = "resource_type"
RESOURCE_ID = "resource_id"
RESOURCE_URL = f"/<{RESOURCE_TYPE}>/<{RESOURCE_ID}>"

dashboard_route = IAMBlueprint(
    "dashboard_route",
    __name__,
    url_prefix="/api/extensions/v1beta/dashboards",
    policy=PolicyType.VIEW_DASHBOARD,
)


@dashboard_route.route(f"{RESOURCE_URL}", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_dashboards.yml")
def retrieve_dashboards(resource_type, resource_id):
    request_object = RetrieveDashboardsRequestObject.from_dict(
        {
            RetrieveDashboardsRequestObject.RESOURCE_TYPE: resource_type.upper(),
            RetrieveDashboardsRequestObject.RESOURCE_ID: resource_id,
            RetrieveDashboardsRequestObject.SUBMITTER: g.authz_user,
        }
    )
    request_object.check_permissions()
    res = RetrieveDashboardsUseCase().execute(request_object)
    res = replace_values(res.value, g.authz_user.localization, in_text_translation=True)
    return jsonify(res), 200


@dashboard_route.route(f"{RESOURCE_URL}/dashboard/<dashboard_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_dashboard.yml")
def retrieve_dashboard(resource_type, resource_id, dashboard_id):
    request_object = RetrieveDashboardRequestObject.from_dict(
        {
            RetrieveDashboardRequestObject.DASHBOARD_ID: dashboard_id,
            RetrieveDashboardRequestObject.RESOURCE_TYPE: resource_type.upper(),
            RetrieveDashboardRequestObject.RESOURCE_ID: resource_id,
            RetrieveDashboardRequestObject.SUBMITTER: g.authz_user,
        }
    )
    request_object.check_permissions()
    res = RetrieveDashboardUseCase().execute(request_object)
    res = replace_values(res.value, g.authz_user.localization, in_text_translation=True)
    return jsonify(res), 200


@dashboard_route.route(f"{RESOURCE_URL}/gadget/<gadget_id>/data", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_gadget_data.yml")
def retrieve_gadget_data(resource_type, resource_id, gadget_id):
    body = {
        **get_request_json_dict_or_raise_exception(request),
        RetrieveGadgetDataRequestObject.GADGET_ID: gadget_id,
        RetrieveGadgetDataRequestObject.ORGANIZATION_ID: resource_id,
        # TODO rework to use resource ID inside use case instead of org id
        RetrieveGadgetDataRequestObject.RESOURCE_TYPE: resource_type.upper(),
        RetrieveGadgetDataRequestObject.RESOURCE_ID: resource_id,
        RetrieveGadgetDataRequestObject.SUBMITTER: g.authz_user,
    }

    request_object = RetrieveGadgetDataRequestObject.from_dict(body)
    request_object.check_permissions()
    res = RetrieveGadgetDataUseCase().execute(request_object)
    res = replace_values(
        res.value.to_dict(include_none=False),
        g.authz_user.localization,
        key_translation=True,
        in_text_translation=True,
    )
    return jsonify(res), 200
