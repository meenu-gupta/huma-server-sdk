import logging

from flask import Blueprint, jsonify, request

from extensions.exceptions import UserDoesNotExist
from extensions.identity_verification.router.identity_verification_requests import (
    OnfidoCallBackVerificationRequestObject,
)
from extensions.identity_verification.router.policies import check_onfido_signature
from extensions.identity_verification.use_cases.receive_onfido_result_use_case import (
    ReceiveOnfidoResultUseCase,
)
from sdk.common.utils.flask_request_utils import validate_request_body_type_is_object

api = Blueprint(
    "identity_verification_public_route",
    __name__,
    url_prefix="/api/identity-verification-public/v1beta",
)

log = logging.getLogger(__name__)


@api.route("/receive-onfido-result", methods=["POST"])
def receive_onfido_result():
    check_onfido_signature()

    body = validate_request_body_type_is_object(request)
    request_obj = OnfidoCallBackVerificationRequestObject.from_dict(body)
    try:
        ReceiveOnfidoResultUseCase().execute(request_obj)
    except UserDoesNotExist:
        log.info("No such user")
    return jsonify({}), 200
