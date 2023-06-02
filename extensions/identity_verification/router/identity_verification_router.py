from flasgger import swag_from
from flask import g, jsonify, request

from extensions.authorization.router.policies import get_default_profile_policy
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.identity_verification.models.identity_verification import (
    IdentityVerificationAction,
)
from extensions.identity_verification.router.identity_verification_requests import (
    GenerateIdentityVerificationTokenRequestObject,
    CreateVerificationLogRequestObject,
)
from extensions.identity_verification.use_cases.create_user_verification_log_use_case import (
    CreateVerificationLogUseCase,
)
from extensions.identity_verification.use_cases.generate_identity_verification_sdk_token_use_case import (
    GenerateIdentityVerificationSdkTokenUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "identity_route",
    __name__,
    url_prefix="/api/identity-verification/v1beta",
    policy=get_default_profile_policy,
)


@api.route("/generate-identity-verification-sdk-token", methods=["POST"])
@audit(IdentityVerificationAction.GenerateIdentityVerificationToken)
@swag_from(f"{SWAGGER_DIR}/generate_identity_verification_sdk_token.yml")
def generate_identity_verification_sdk_token():
    data = get_request_json_dict_or_raise_exception(request)
    user_agent = g.get("user_agent")
    application_id = user_agent.bundle_id if user_agent else None
    data.update(
        {
            GenerateIdentityVerificationTokenRequestObject.USER_ID: g.user.id,
            GenerateIdentityVerificationTokenRequestObject.APPLICATION_ID: application_id,
        }
    )
    request_obj = GenerateIdentityVerificationTokenRequestObject.from_dict(data)
    response = GenerateIdentityVerificationSdkTokenUseCase().execute(request_obj)
    return jsonify(response.value.to_dict()), 201


@api.route("/user-verification-log", methods=["POST"])
@audit(IdentityVerificationAction.CreateUserVerificationLog)
@swag_from(f"{SWAGGER_DIR}/create_user_verification_log.yml")
def create_user_verification_log():
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CreateVerificationLogRequestObject.USER_ID: g.user.id})
    request_obj = CreateVerificationLogRequestObject.from_dict(body)
    response = CreateVerificationLogUseCase().execute(request_obj)
    return jsonify(response.value), 201
