from flask import Blueprint, jsonify, request

from sdk.common.decorator.debug_route import debug_route
from sdk.common.utils import inject
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.versioning.models.version import Version
from sdk.versioning.router.versioning_requests import IncreaseVersionRequestObject
from sdk.versioning.use_case.versioning_use_case import IncreaseVersionUseCase

version_blueprint = Blueprint("version_router", __name__, url_prefix="/version")


@version_blueprint.route("", methods=["GET"])
def retrieve_version():
    version = inject.instance(Version)
    response = version.to_dict(include_none=False)
    return jsonify(response), 200


@version_blueprint.route("/ping", methods=["GET"])
def ping_pong():
    return "pong", 200


@version_blueprint.route("", methods=["POST"])
@debug_route()
def increase_version():
    body = get_request_json_dict_or_raise_exception(request)
    req_obj = IncreaseVersionRequestObject.from_dict(remove_none_values(body))
    IncreaseVersionUseCase().execute(req_obj)

    return "", 200
