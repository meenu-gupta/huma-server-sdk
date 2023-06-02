from io import BytesIO

from flasgger import swag_from
from flask import request, make_response, send_file, jsonify, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.router.policies import (
    get_identified_export_data,
    check_identified_task_result,
    get_export_permission,
)
from extensions.export_deployment.use_case.export_profile_use_cases import (
    UpdateExportProfileUseCase,
    DeleteExportProfileUseCase,
    RetrieveExportProfilesUseCase,
    CreateExportProfileUseCase,
)
from extensions.export_deployment.use_case.export_request_objects import (
    RunExportTaskRequestObject,
    CheckExportDeploymentTaskStatusRequestObject,
    RetrieveExportDeploymentProcessesRequestObject,
    CreateExportProfileRequestObject,
    UpdateExportProfileRequestObject,
    DeleteExportProfileRequestObject,
    RetrieveExportProfilesRequestObject,
    ExportUsersRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
    RunExportTaskUseCase,
    CheckExportTaskStatusUseCase,
    RetrieveExportDeploymentProcessesUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    validate_request_body_type_is_object,
)
from sdk.common.utils.validators import remove_none_values

api = IAMBlueprint(
    "export_deployment_route",
    __name__,
    url_prefix="/api/extensions/v1beta/export",
    policy=PolicyType.EXPORT_PATIENT_DATA,
)


@api.route("/deployment/<deployment_id>", methods=["POST"])
@api.require_policy(get_identified_export_data)
@swag_from(f"{SWAGGER_DIR}/export_deployment.yml")
def export_deployment(deployment_id):
    body = validate_request_body_type_is_object(request)
    data = remove_none_values(
        {**body, ExportUsersRequestObject.DEPLOYMENT_ID: deployment_id}
    )
    request_object = ExportUsersRequestObject.from_dict(data)
    use_case = ExportDeploymentUseCase()
    response_object = use_case.execute(request_object)
    return make_response(
        send_file(
            BytesIO(response_object.value.content),
            attachment_filename=response_object.value.filename,
            as_attachment=False,
            mimetype=response_object.value.contentType,
        )
    )


@api.route("/", methods=["POST"])
@api.require_policy(get_export_permission)
@swag_from(f"{SWAGGER_DIR}/export.yml")
def export():
    body = validate_request_body_type_is_object(request)

    request_object = ExportUsersRequestObject.from_dict(body)
    use_case = ExportDeploymentUseCase()
    response_object = use_case.execute(request_object)
    return make_response(
        send_file(
            BytesIO(response_object.value.content),
            attachment_filename=response_object.value.filename,
            as_attachment=False,
            mimetype=response_object.value.contentType,
        )
    )


@api.route("/deployment/<deployment_id>/task", methods=["POST"])
@api.require_policy(get_identified_export_data)
@swag_from(f"{SWAGGER_DIR}/run_export_deployment_task.yml")
def run_export_deployment_task(deployment_id):
    body = validate_request_body_type_is_object(request)
    request_object = RunExportTaskRequestObject.from_dict(
        remove_none_values(
            {
                **body,
                RunExportTaskRequestObject.DEPLOYMENT_ID: deployment_id,
                RunExportTaskRequestObject.REQUESTER_ID: str(g.user.id),
                RunExportTaskRequestObject.EXPORT_TYPE: ExportProcess.ExportType.DEFAULT.value,
            }
        )
    )
    use_case = RunExportTaskUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/deployment/<deployment_id>/task/<export_process_id>", methods=["GET"])
@api.require_policy(check_identified_task_result)
@swag_from(f"{SWAGGER_DIR}/check_export_deployment_status.yml")
def check_export_deployment_task_status(deployment_id, export_process_id):
    body = validate_request_body_type_is_object(request)
    request_object = CheckExportDeploymentTaskStatusRequestObject.from_dict(
        remove_none_values(
            {
                **body,
                CheckExportDeploymentTaskStatusRequestObject.EXPORT_PROCESS_ID: export_process_id,
                CheckExportDeploymentTaskStatusRequestObject.DEPLOYMENT_ID: deployment_id,
            }
        )
    )
    use_case = CheckExportTaskStatusUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/deployment/<deployment_id>/task", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_export_deployment_processes.yml")
def retrieve_export_deployment_processes(deployment_id):
    request_object = RetrieveExportDeploymentProcessesRequestObject.from_dict(
        {
            RetrieveExportDeploymentProcessesRequestObject.DEPLOYMENT_ID: deployment_id,
        }
    )

    use_case = RetrieveExportDeploymentProcessesUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200


@api.route("/profile", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/create_export_profile.yml")
def create_export_profile():
    data = validate_request_body_type_is_object(request)
    request_object = CreateExportProfileRequestObject.from_dict(
        remove_none_values(data)
    )
    use_case = CreateExportProfileUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict()), 201


@api.route("/profile/<profile_id>", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/update_export_profile.yml")
def update_export_profile(profile_id):
    body = validate_request_body_type_is_object(request)
    data = {
        **body,
        UpdateExportProfileRequestObject.ID: profile_id,
    }
    request_object = UpdateExportProfileRequestObject.from_dict(
        remove_none_values(data)
    )
    use_case = UpdateExportProfileUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict()), 200


@api.route("/profile/<profile_id>", methods=["DELETE"])
@swag_from(f"{SWAGGER_DIR}/delete_export_profile.yml")
def delete_export_profile(profile_id):
    data = {
        DeleteExportProfileRequestObject.PROFILE_ID: profile_id,
    }
    request_object = DeleteExportProfileRequestObject.from_dict(data)
    use_case = DeleteExportProfileUseCase()
    use_case.execute(request_object)
    return "", 204


@api.route("/profile/search", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_export_profiles.yml")
def retrieve_export_deployment_profiles():
    data = validate_request_body_type_is_object(request)
    request_object = RetrieveExportProfilesRequestObject.from_dict(
        remove_none_values(data)
    )

    use_case = RetrieveExportProfilesUseCase()
    response_object = use_case.execute(request_object)
    return jsonify(response_object.value.to_dict(include_none=False)), 200
