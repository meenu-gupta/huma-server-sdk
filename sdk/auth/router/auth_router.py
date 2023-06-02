import logging

from flasgger import swag_from
from flask import Blueprint, request, jsonify
from jwt import InvalidSignatureError

from sdk.auth.model.auth_user import AuthAction
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.use_case.auth_request_objects import (
    SignUpRequestObject,
    SendVerificationTokenRequestObject,
    SignInRequestObject,
    AuthProfileRequestObject,
    RefreshTokenRequestObject,
    SignOutRequestObject,
    SignOutRequestObjectV1,
    RequestPasswordResetRequestObject,
    ConfirmationRequestObject,
    ResetPasswordRequestObject,
    SetAuthAttributesRequestObject,
    CheckAuthAttributesRequestObject,
    GenerateAuthKeysRequestObject,
    CreateServiceAccountRequestObject,
    inject_language,
    SignInRequestObjectV1,
    RefreshTokenRequestObjectV1,
)
from sdk.auth.use_case.auth_use_cases import (
    SignUpUseCase,
    SendVerificationTokenUseCase,
    AuthProfileUseCase,
    RefreshTokenUseCase,
    SignOutUseCase,
    SignOutUseCaseV1,
    SessionUseCase,
    ConfirmationUseCase,
    SetAuthAttributesUseCase,
    CheckAuthAttributesUseCase,
    GenerateAuthTokenUseCase,
    CreateServiceAccountUseCase,
    RefreshTokenUseCaseV1,
)
from sdk.auth.use_case.factories import (
    sign_in_use_case_factory,
    sign_in_use_case_factory_v1,
)
from sdk.auth.use_case.password_reset import (
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.exceptions.exceptions import DetailedException
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
    get_http_user_agent_from_request,
)
from sdk.phoenix.audit_logger import audit, AuditLog

api = Blueprint("auth_route", __name__, url_prefix="/api/auth/v1beta")
api_v1 = Blueprint("auth_route_v1", __name__, url_prefix="/api/auth/v1")
logger = logging.getLogger(__name__)


@api.errorhandler(InvalidSignatureError)
def invalid_signature(e):
    logger.info(e)
    exec_to_return = DetailedException(100010, "InvalidSignatureError", 401)
    return jsonify(exec_to_return.to_dict()), exec_to_return.status_code


def inject_extra_fields(body: dict):
    inject_language(body)
    body[DeviceSession.DEVICE_AGENT] = get_http_user_agent_from_request(request)


@api.route("/signup", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/sign_up.yml")
def sign_up():
    body = get_request_json_dict_or_raise_exception(request)
    inject_language(body)

    sign_up_data = SignUpRequestObject.from_dict(body)
    response = SignUpUseCase().execute(sign_up_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/sendverificationtoken", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/send_verification_token.yml")
def send_verification_token():
    body = get_request_json_dict_or_raise_exception(request)
    inject_language(body)

    verification_token_data = SendVerificationTokenRequestObject.from_dict(body)
    response = SendVerificationTokenUseCase().execute(verification_token_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/signin", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/sign_in.yml")
def sign_in():
    body = get_request_json_dict_or_raise_exception(request)
    inject_extra_fields(body)
    sign_in_data = SignInRequestObject.from_dict(body)
    use_case = sign_in_use_case_factory(sign_in_data.method, sign_in_data.authStage)
    response = use_case.execute(sign_in_data)
    AuditLog.create_log(
        action=AuthAction.SignIn, user_id=response.value.uid, secure=True
    )
    return jsonify(response.value.to_dict(include_none=False)), 200


@api_v1.route("/signin", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/sign_in_v1.yml")
def sign_in_v1():
    body = get_request_json_dict_or_raise_exception(request)
    inject_extra_fields(body)
    sign_in_data = SignInRequestObjectV1.from_dict(body)
    use_case = sign_in_use_case_factory_v1(sign_in_data.method, sign_in_data.authStage)
    response = use_case.execute(sign_in_data)
    AuditLog.create_log(
        action=AuthAction.SignIn, user_id=response.value.uid, secure=True
    )
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/confirm", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/confirmation.yml")
def confirmation():
    body = get_request_json_dict_or_raise_exception(request)
    inject_extra_fields(body)
    confirmation_data = ConfirmationRequestObject.from_dict(body)
    response = ConfirmationUseCase().execute(confirmation_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/request-password-reset", methods=["POST"])
@audit(AuthAction.RequestPasswordReset)
@swag_from(f"{SWAGGER_DIR}/request_password_reset.yml")
def request_password_reset():
    body = get_request_json_dict_or_raise_exception(request)
    inject_language(body)
    password_reset_data = RequestPasswordResetRequestObject.from_dict(body)
    response = RequestPasswordResetUseCase().execute(password_reset_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/password-reset", methods=["POST"])
@audit(AuthAction.PasswordReset, secure=True)
@swag_from(f"{SWAGGER_DIR}/reset_password.yml")
def password_reset():
    body = get_request_json_dict_or_raise_exception(request)
    reset_password_data = ResetPasswordRequestObject.from_dict(body)
    response = ResetPasswordUseCase().execute(reset_password_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/refreshtoken", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/refresh_token.yml")
def refresh_token():
    body = get_request_json_dict_or_raise_exception(request)
    inject_extra_fields(body)
    refresh_token_data = RefreshTokenRequestObject.from_dict(body)
    response = RefreshTokenUseCase().execute(refresh_token_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api_v1.route("/refreshtoken", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/refresh_token_v1.yml")
def refresh_token_v1():
    body = get_request_json_dict_or_raise_exception(request)
    inject_extra_fields(body)
    refresh_token_data = RefreshTokenRequestObjectV1.from_dict(body)
    response = RefreshTokenUseCaseV1().execute(refresh_token_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/authprofile", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/auth_profile.yml")
def auth_profile():
    """
    Get Profile Id By Token
    """
    body = get_request_json_dict_or_raise_exception(request)
    auth_profile_data = AuthProfileRequestObject.from_dict(body)
    response = AuthProfileUseCase().execute(auth_profile_data)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/signout", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/sign_out.yml")
def sign_out():
    body = get_request_json_dict_or_raise_exception(request)
    user_agent = get_http_user_agent_from_request(request)
    body[DeviceSession.DEVICE_AGENT] = user_agent
    sign_out_data = SignOutRequestObject.from_dict(body)
    session_id: str = SignOutUseCase().execute(sign_out_data)
    return jsonify({"id": session_id}), 200


@api_v1.route("/signout", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/sign_out_v1.yml")
def sign_out_v1():
    body = get_request_json_dict_or_raise_exception(request)
    user_agent = get_http_user_agent_from_request(request)
    body[DeviceSessionV1.DEVICE_AGENT] = user_agent
    sign_out_data = SignOutRequestObjectV1.from_dict(body)
    session_id: str = SignOutUseCaseV1().execute(sign_out_data)
    return jsonify({"id": session_id}), 200


@api.route("/user/<user_id>/sessions", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_sessions.yml")
def retrieve_sessions(user_id):
    sessions = SessionUseCase().execute(user_id)
    ignored_fields = [DeviceSession.ID, DeviceSession.USER_ID]
    response = [
        session.to_dict(include_none=False, ignored_fields=ignored_fields)
        for session in sessions
    ]
    return jsonify(response), 200


@api.route("/set-auth-attributes", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/set_auth_attributes.yml")
def set_auth_attributes():
    """Allows to set auth attributes if were not set before"""
    body = get_request_json_dict_or_raise_exception(request)
    inject_language(body)
    request_object = SetAuthAttributesRequestObject.from_dict(body)
    response = SetAuthAttributesUseCase().execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/check-auth-attributes", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/check_auth_attributes.yml")
def check_auth_attributes():
    """Allows to check that user have all needed attributes for MFA"""
    body = get_request_json_dict_or_raise_exception(request)
    request_object = CheckAuthAttributesRequestObject.from_dict(body)
    response = CheckAuthAttributesUseCase().execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 200


@api.route("/user/<user_id>/token", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/generate_auth_token.yml")
def generate_auth_token(user_id: str):
    request_object = GenerateAuthKeysRequestObject.from_dict(
        {GenerateAuthKeysRequestObject.USER_ID: user_id}
    )
    response = GenerateAuthTokenUseCase().execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 201


@api.route("/service-account", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/create_service_account.yml")
def create_service_account():
    body = get_request_json_dict_or_raise_exception(request)
    request_object = CreateServiceAccountRequestObject.from_dict(body)
    response = CreateServiceAccountUseCase().execute(request_object)

    return jsonify(response.value.to_dict(include_none=False)), 201
