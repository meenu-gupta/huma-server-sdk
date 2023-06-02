from flasgger import swag_from
from flask import request, g, send_file, jsonify

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.common.policies import deny_not_self
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.export_deployment.router.log_actions import SummaryReportAction
from extensions.export_deployment.router.utils import enable_if_configured_or_404
from extensions.export_deployment.use_case.async_summary_report_use_case import (
    RunSummaryReportTaskUseCase,
)
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportRequestObject,
)
from extensions.export_deployment.use_case.summary_report_use_case import (
    GenerateSummaryReportUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "report_route",
    __name__,
    url_prefix="/api/extensions/v1beta/report",
    policy=[PolicyType.GENERATE_HEALTH_REPORT, deny_not_self],
    template_folder="../templates",
)


@api.post("/summary/user/<user_id>")
@audit(SummaryReportAction.CreateSummaryReport, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/generate_summary_report.yml")
@enable_if_configured_or_404
def generate_report(user_id: str):
    body = {
        **get_request_json_dict_or_raise_exception(request),
        GenerateSummaryReportRequestObject.USER: g.path_user,
        GenerateSummaryReportRequestObject.REQUESTER_ID: g.user.id,
        GenerateSummaryReportRequestObject.DEPLOYMENT: g.authz_path_user.deployment,
    }
    request_object = GenerateSummaryReportRequestObject.from_dict(body)
    use_case = GenerateSummaryReportUseCase()
    response_object = use_case.execute(request_object)
    response = send_file(
        response_object.value.content, attachment_filename="SummaryReport.pdf"
    )
    return response, 201


@api.post("/summary/user/<user_id>/task")
@audit(SummaryReportAction.RunAsyncSummaryReport, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/async_summary_report.yml")
@enable_if_configured_or_404
def generate_report_async(user_id: str):
    body = {
        **get_request_json_dict_or_raise_exception(request),
        GenerateSummaryReportRequestObject.USER: g.path_user,
        GenerateSummaryReportRequestObject.REQUESTER_ID: g.user.id,
        GenerateSummaryReportRequestObject.DEPLOYMENT: g.authz_path_user.deployment,
    }
    request_object = GenerateSummaryReportRequestObject.from_dict(body)
    use_case = RunSummaryReportTaskUseCase()
    response_object = use_case.execute(request_object)
    return jsonify({"exportProcessId": response_object.value}), 201
