from uuid import uuid4
from flasgger import swag_from
from flask import jsonify, request, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.common.policies import (
    get_user_route_read_policy,
    get_user_route_write_policy,
)
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive import Action
from extensions.module_result.router.module_result_requests import (
    AggregateModuleResultsRequestObjects,
    RetrieveModuleResultsRequestObject,
    SearchModuleResultsRequestObject,
    RetrieveModuleResultRequestObject,
    CreateModuleResultRequestObject,
    RetrieveUnseenModuleResultRequestObject,
)
from extensions.module_result.service.module_result_service import ModuleResultService
from extensions.module_result.use_cases.retrieve_module_results_use_case import (
    RetrieveModuleResultUseCase,
    process_ecg_primitive,
)
from extensions.module_result.use_cases.search_module_results_use_case import (
    SearchModuleResultsUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.usecase.response_object import Response
from sdk.common.utils.flask_request_utils import (
    get_request_json_list_or_raise_exception,
    validate_request_body_type_is_object,
)
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "modules_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=get_user_route_read_policy,
)


@api.route("/<user_id>/module-result/<module_id>", methods=["POST"])
@api.require_policy(get_user_route_write_policy)
@audit(Action.CreateModuleResult)
@swag_from(f"{SWAGGER_DIR}/create_module_results.yml")
def create_module_result(user_id: str, module_id: str):
    RequestObject = CreateModuleResultRequestObject

    raw_module_result = get_request_json_list_or_raise_exception(request)

    module_config_id = dict(request.args).get(RequestObject.MODULE_CONFIG_ID)

    module_result_id = uuid4().hex

    additional_data = {
        Primitive.USER_ID: user_id,
        Primitive.MODULE_ID: module_id,
        Primitive.MODULE_RESULT_ID: module_result_id,
        Primitive.SUBMITTER_ID: g.user.id,
        Primitive.CLIENT: g.get("user_agent", None),
    }

    for item in raw_module_result:
        item.update(remove_none_values(additional_data))

    req_data = {
        RequestObject.DEPLOYMENT: g.authz_user.deployment,
        RequestObject.MODULE_CONFIG_ID: module_config_id,
        RequestObject.MODULE_ID: module_id,
        RequestObject.RAW_DATA: raw_module_result,
        RequestObject.USER: g.path_user,
        RequestObject.LANGUAGE: g.user.language,
    }

    req_obj = CreateModuleResultRequestObject.from_dict(remove_none_values(req_data))
    response = ModuleResultService().create_module_result(req_obj)
    if "errors" in response:
        response["errors"].extend(req_obj.errors)
    elif req_obj.errors:
        response["errors"] = req_obj.errors

    return jsonify(response), 201


@api.route("/<user_id>/flagged-modules", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_unseen_module_result.yml")
def retrieve_unseen_module_results(user_id: str):
    user: AuthorizedUser = g.authz_user
    module_configs = user.deployment.moduleConfigs
    hybrid_questionnaire_module_ids = [
        mc.id for mc in module_configs if mc.is_hybrid_questionnaire()
    ]
    enabled_modules = [mc.id for mc in module_configs]

    request_object_dict = {
        RetrieveUnseenModuleResultRequestObject.USER_ID: user_id,
        RetrieveUnseenModuleResultRequestObject.DEPLOYMENT_ID: user.deployment_id(),
        RetrieveUnseenModuleResultRequestObject.HYBRID_QUESTIONNAIRE_MODULE_IDS: hybrid_questionnaire_module_ids,
        RetrieveUnseenModuleResultRequestObject.ENABLED_MODULE_IDS: enabled_modules,
    }
    request_object: RetrieveUnseenModuleResultRequestObject = (
        RetrieveUnseenModuleResultRequestObject.from_dict(request_object_dict)
    )
    module_service = ModuleResultService()
    response = module_service.retrieve_unseen_module_results(request_object)
    return jsonify(remove_none_values(response.to_dict())), 200


@api.route("/<user_id>/module-result/<module_id>/search", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_module_results.yml")
def retrieve_module_results(user_id: str, module_id: str):
    user: AuthorizedUser = g.authz_user

    request_object_dict = validate_request_body_type_is_object(request)
    additional_data = {
        RetrieveModuleResultsRequestObject.USER_ID: user_id,
        RetrieveModuleResultsRequestObject.MODULE_ID: module_id,
        RetrieveModuleResultsRequestObject.DEPLOYMENT_ID: user.deployment_id(),
        RetrieveModuleResultsRequestObject.ROLE: user.get_role().id,
    }
    request_object_dict.update(additional_data)

    normal_key = RetrieveModuleResultsRequestObject.NORMAL_QUESTIONNAIRES
    if normal_key in request_object_dict and request_object_dict[normal_key]:
        module_configs = user.deployment.moduleConfigs
        hybrid_questionnaire_module_ids = [
            mc.id for mc in module_configs if mc.is_hybrid_questionnaire()
        ]
        exclude_key = RetrieveModuleResultsRequestObject.EXCLUDE_MODULE_IDS
        request_object_dict[exclude_key] = hybrid_questionnaire_module_ids

    request_object: RetrieveModuleResultsRequestObject = (
        RetrieveModuleResultsRequestObject.from_dict(request_object_dict)
    )
    module_service = ModuleResultService()

    result = module_service.retrieve_module_results(
        request_object.userId,
        request_object.moduleId,
        request_object.skip,
        request_object.limit,
        request_object.direction,
        request_object.fromDateTime,
        request_object.toDateTime,
        request_object.filters,
        request_object.deploymentId,
        request_object.role,
        request_object.excludedFields,
        request_object.moduleConfigId,
        request_object.excludeModuleIds,
        request_object.unseenOnly,
    )
    converted_primitives = _convert_primitives(result)
    translated_primitives = replace_values(
        converted_primitives, g.authz_user.localization, string_list_translator=True
    )
    response_json = jsonify(translated_primitives)
    return response_json, 200


@api.route("/<user_id>/module-result/search", methods=["POST"])
def search_module_results(user_id: str):
    user: AuthorizedUser = g.authz_user

    request_object_dict = validate_request_body_type_is_object(request)
    additional_data = {
        SearchModuleResultsRequestObject.USER_ID: user_id,
        SearchModuleResultsRequestObject.DEPLOYMENT_ID: user.deployment_id(),
        SearchModuleResultsRequestObject.ROLE: user.get_role().id,
    }
    request_object_dict.update(additional_data)
    request_object = SearchModuleResultsRequestObject.from_dict(request_object_dict)
    response: Response = SearchModuleResultsUseCase().execute(request_object)

    response_json = jsonify(_convert_primitives(response.value))
    response_json = replace_values(response_json, g.authz_user.localization)
    return response_json, 200


@api.route("/<user_id>/module-result/aggregate", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/aggregate_module_results.yml")
def retrieve_aggregated(user_id: str):
    body = validate_request_body_type_is_object(request)
    body.update({AggregateModuleResultsRequestObjects.USER_ID: user_id})
    request_object: AggregateModuleResultsRequestObjects = (
        AggregateModuleResultsRequestObjects.from_dict(body)
    )
    results = ModuleResultService().retrieve_aggregated_results(
        primitive_name=request_object.primitiveName,
        module_config_id=request_object.moduleConfigId,
        aggregation_function=request_object.function,
        mode=request_object.mode,
        start_date=request_object.fromDateTime,
        end_date=request_object.toDateTime,
        skip=request_object.skip,
        limit=request_object.limit,
        user_id=request_object.userId,
        timezone=request_object.timezone,
    )

    return jsonify(results), 200


@api.route("/<user_id>/primitive/<primitive_type>/<module_result_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_module_result.yml")
def retrieve_module_result(user_id: str, primitive_type: str, module_result_id: str):
    request_data = {
        RetrieveModuleResultRequestObject.USER_ID: user_id,
        RetrieveModuleResultRequestObject.MODULE_RESULT_ID: module_result_id,
        RetrieveModuleResultRequestObject.PRIMITIVE_TYPE: primitive_type,
    }

    request_object = RetrieveModuleResultRequestObject.from_dict(request_data)
    use_case = RetrieveModuleResultUseCase()
    result = use_case.execute(request_object)
    result_data = result.value.to_dict(
        ignored_fields=(
            Primitive.ID,
            Primitive.USER_ID,
            Primitive.SUBMITTER_ID,
            Primitive.DEPLOYMENT_ID,
        )
    )
    return jsonify(result_data), 200


def _convert_primitives(primitive_dict: dict[str, list[Primitive]]) -> dict:
    result_dict = {}
    for primitive_name, primitives in primitive_dict.items():
        result_dict[primitive_name] = []
        for primitive in primitives:
            primitive = process_ecg_primitive(primitive)
            primitive_data = primitive.to_dict(
                include_none=False,
                ignored_fields=(
                    Primitive.ID,
                    Primitive.USER_ID,
                    Primitive.SUBMITTER_ID,
                    Primitive.DEPLOYMENT_ID,
                ),
            )
            result_dict[primitive_name].append(primitive_data)
    return result_dict
