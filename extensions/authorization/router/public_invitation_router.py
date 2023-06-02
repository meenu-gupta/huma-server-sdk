from flasgger import swag_from
from flask import Blueprint, jsonify
from flask_limiter import Limiter

from extensions.authorization.router.invitation_request_objects import (
    InvitationValidityRequestObject,
)
from extensions.authorization.use_cases.invitation_validity_check_use_case import (
    InvitationValidityUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils import inject

api = Blueprint(
    "invitation_public_route",
    __name__,
    url_prefix="/api/public/v1beta/",
)


@api.before_app_first_request
def init_limit():
    limiter = inject.instance(Limiter)
    limiter.limit("4/minute")(api)


@api.route("/invitation-validity/<invitation_code>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/invitation_validity_check.yml")
def invitation_validity_check(invitation_code):
    request_object = InvitationValidityRequestObject.from_dict(
        {InvitationValidityRequestObject.INVITATION_CODE: invitation_code}
    )
    response_object = InvitationValidityUseCase().execute(request_object)
    return jsonify(response_object.value.to_dict()), 200
