from flasgger import swag_from
from flask import jsonify, request, g

from extensions.common.policies import custom_module_config_policy
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.module_result.models.action import CustomModuleConfigAction
from extensions.module_result.router.custom_module_config_requests import (
    CreateOrUpdateCustomModuleConfigRequestObject,
    RetrieveCustomModuleConfigsRequestObject,
    RetrieveModuleConfigLogsRequestObject,
    DEFAULT_CUSTOM_MODULE_CONFIG_LOG_RESULT_PAGE_SIZE,
)
from extensions.module_result.use_cases.create_or_update_custom_module_config_use_case import (
    CreateOrUpdateCustomModuleConfigUseCase,
)
from extensions.module_result.use_cases.retrieve_custom_module_configs_use_case import (
    RetrieveCustomModuleConfigsUseCase,
)
from extensions.module_result.use_cases.retrieve_module_config_logs_use_case import (
    RetrieveModuleConfigLogsUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import validate_request_body_type_is_object
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "custom_module_config_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=custom_module_config_policy,
)


@api.put("/<user_id>/moduleConfig/<module_config_id>")
@audit(CustomModuleConfigAction.CreateOrUpdateCustomModuleConfig, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/create_or_update_user_module_config.yml")
def create_or_update_custom_module_config_for_user(user_id: str, module_config_id: str):
    feature_flags = g.authz_user.deployment.features
    if not (feature_flags and feature_flags.personalizedConfig):
        return "<h1>Feature is not enabled</h1>", 404

    req_body = validate_request_body_type_is_object(request)
    body = remove_none_values(req_body)
    body.update(
        {
            CreateOrUpdateCustomModuleConfigRequestObject.ID: module_config_id,
            CreateOrUpdateCustomModuleConfigRequestObject.USER_ID: user_id,
            CreateOrUpdateCustomModuleConfigRequestObject.USER: g.authz_path_user,
            CreateOrUpdateCustomModuleConfigRequestObject.CLINICIAN_ID: g.authz_user.id,
        }
    )

    request_object = CreateOrUpdateCustomModuleConfigRequestObject.from_dict(body)
    request_object.check_permissions()
    response = CreateOrUpdateCustomModuleConfigUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@api.get("/<user_id>/moduleConfig/<module_config_id>/logs")
@audit(CustomModuleConfigAction.RetrieveModuleConfigLogs, target_key="user_id")
@swag_from(f"{SWAGGER_DIR}/retrieve_custom_module_config_logs.yml")
def retrieve_custom_module_config_logs_for_user(user_id: str, module_config_id: str):
    feature_flags = g.authz_user.deployment.features
    if not (feature_flags and feature_flags.personalizedConfig):
        return "<h1>Feature is not enabled</h1>", 404

    args = request.args or {}
    skip = int(args.get(RetrieveModuleConfigLogsRequestObject.SKIP, 0))
    limit = int(
        args.get(
            RetrieveModuleConfigLogsRequestObject.LIMIT,
            DEFAULT_CUSTOM_MODULE_CONFIG_LOG_RESULT_PAGE_SIZE,
        )
    )
    log_type = args.get(RetrieveModuleConfigLogsRequestObject.TYPE)
    body = {
        RetrieveModuleConfigLogsRequestObject.MODULE_CONFIG_ID: module_config_id,
        RetrieveModuleConfigLogsRequestObject.USER_ID: user_id,
        RetrieveModuleConfigLogsRequestObject.SKIP: skip,
        RetrieveModuleConfigLogsRequestObject.LIMIT: limit,
        RetrieveModuleConfigLogsRequestObject.TYPE: log_type,
    }
    body = remove_none_values(body)
    request_object = RetrieveModuleConfigLogsRequestObject.from_dict(body)
    response = RetrieveModuleConfigLogsUseCase().execute(request_object)
    module_config_logs = [
        log.to_dict(include_none=False) for log in response.value.logs
    ]
    return {"logs": module_config_logs, "total": response.value.total}, 200


@api.get("/<user_id>/moduleConfigs")
@swag_from(f"{SWAGGER_DIR}/retrieve_user_module_configs.yml")
def retrieve_custom_module_configs_of_user(user_id: str):
    feature_flags = g.authz_user.deployment.features
    if not (feature_flags and feature_flags.personalizedConfig):
        return "<h1>Feature is not enabled</h1>", 404

    request_object = RetrieveCustomModuleConfigsRequestObject.from_dict(
        {RetrieveCustomModuleConfigsRequestObject.USER_ID: user_id}
    )
    response = RetrieveCustomModuleConfigsUseCase().execute(request_object)
    custom_configs = [conf.to_dict(include_none=False) for conf in response.value]
    return {"configs": custom_configs}, 200
