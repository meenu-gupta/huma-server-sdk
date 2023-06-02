from io import BytesIO

from flasgger import swag_from
from flask import request, make_response, send_file, jsonify, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.common.policies import deny_not_self
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.export_deployment.router.log_actions import ExportDataAction
from extensions.export_deployment.use_case.export_request_objects import (
    ExportUserDataRequestObject,
    RunAsyncUserExportRequestObject,
    CheckUserExportTaskStatusRequestObject,
    RetrieveUserExportProcessesRequestObject,
    ConfirmExportBadgesRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    CheckExportTaskStatusUseCase,
    ExportUserDataUseCase,
    AsyncExportUserDataUseCase,
    RetrieveUserExportProcessesUseCase,
    ConfirmExportBadgesUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    validate_request_body_type_is_object,
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "user_export_route",
    __name__,
    url_prefix="/api/extensions/v1beta/export/user",
    policy=[PolicyType.VIEW_OWN_DATA, deny_not_self],
)


@api.route("/<user_id>", methods=["POST"])
@audit(ExportDataAction.ExportPatientsListData, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/export_user_data.yml")
def export_user_data(user_id):
    body = validate_request_body_type_is_object(request)
    body[ExportUserDataRequestObject.USER_ID] = user_id

    request_object = ExportUserDataRequestObject.from_dict(body)
    use_case = ExportUserDataUseCase()
    response_object = use_case.execute(request_object)
    return (
        make_response(
            send_file(
                BytesIO(response_object.value.content),
                attachment_filename=response_object.value.filename,
                as_attachment=False,
                mimetype=response_object.value.contentType,
            )
        ),
        200,
    )


@api.route("/<user_id>/task", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/async_user_export.yml")
def export_user_data_async(user_id):
    body = validate_request_body_type_is_object(request)
    request_object = RunAsyncUserExportRequestObject.from_dict(
        remove_none_values(
            {
                **body,
                RunAsyncUserExportRequestObject.USER_ID: user_id,
                RunAsyncUserExportRequestObject.REQUESTER_ID: g.user.id,
            }
        )
    )

    use_case = AsyncExportUserDataUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/<user_id>/task/<export_process_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/check_user_export_task_status.yml")
def check_user_export_task_status(user_id, export_process_id):
    body = validate_request_body_type_is_object(request)
    request_object = CheckUserExportTaskStatusRequestObject.from_dict(
        remove_none_values(
            {
                **body,
                CheckUserExportTaskStatusRequestObject.EXPORT_PROCESS_ID: export_process_id,
                CheckUserExportTaskStatusRequestObject.USER_ID: user_id,
            }
        )
    )
    use_case = CheckExportTaskStatusUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/<user_id>/task", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_user_export_processes.yml")
def retrieve_user_export_processes(user_id):
    request_object = RetrieveUserExportProcessesRequestObject.from_dict(
        {
            RetrieveUserExportProcessesRequestObject.USER_ID: user_id,
        }
    )

    use_case = RetrieveUserExportProcessesUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/<user_id>/badges/confirm", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/confirm_badges.yml")
def confirm_badges(user_id):
    body = get_request_json_dict_or_raise_exception(request)
    body[ConfirmExportBadgesRequestObject.REQUESTER_ID] = user_id
    request_object = ConfirmExportBadgesRequestObject.from_dict(body)
    use_case = ConfirmExportBadgesUseCase()
    rsp = use_case.execute(request_object)
    return jsonify(rsp.to_dict()), 200
