from flasgger import swag_from
from flask import request, jsonify, g

from extensions.autocomplete.router.autocomplete_requests import (
    SearchAutocompleteRequestObject,
    UpdateAutoCompleteSearchMetadataRequestObject,
)
from extensions.autocomplete.use_cases.search_autocomplete_result_use_case import (
    SearchAutocompleteResultUseCase,
)
from extensions.autocomplete.use_cases.update_autocomplete_metadata_use_case import (
    UpdateAutoCompleteMetadataUseCase,
)
from extensions.common.policies import get_user_route_read_policy
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)

api = IAMBlueprint(
    "autocomplete_route",
    __name__,
    url_prefix="/api/autocomplete/v1beta",
    policy=get_user_route_read_policy,
)


@api.route("/search", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_autocomplete_search_result.yml")
def retrieve_autocomplete():
    body = get_request_json_dict_or_raise_exception(request)
    body[SearchAutocompleteRequestObject.LANGUAGE] = g.authz_user.get_language()
    request_obj = SearchAutocompleteRequestObject.from_dict(body)
    result = SearchAutocompleteResultUseCase().execute(request_obj)
    return jsonify(result.value), 200


@api.route("/update", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/update_autocomplete_metadata.yml")
def update_autocomplete_metadata():
    body = get_request_json_dict_or_raise_exception(request)
    request_obj = UpdateAutoCompleteSearchMetadataRequestObject.from_dict(body)
    response = UpdateAutoCompleteMetadataUseCase().execute(request_obj)

    return jsonify({"ids": response.value}), 200
