import logging
from functools import wraps

import mohawk
from flask import g, request
from sentry_sdk import set_user

from sdk.auth.enums import AuthStage, Method
from sdk.auth.events.token_extraction_event import TokenExtractionEvent
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_use_cases import (
    get_client,
    check_project,
    check_token_issued_after_password_update,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.sentry.sentry_adapter import SentryAdapter
from sdk.common.adapter.token.helper import verify_jwt_in_request
from sdk.common.exceptions.exceptions import (
    DetailedException,
    InvalidRequestException,
    UnauthorizedException,
    WrongTokenException,
    AccessTokenNotValidForMultiFactorAuthException,
)
from sdk.common.utils import inject
from sdk.common.utils.token.exceptions import NoAuthorizationError
from sdk.common.utils.token.hawk.hawk import get_hawk_receiver, UserKey
from sdk.common.utils.token.jwt.exceptions import InvalidHeaderError
from sdk.common.utils.token.jwt.jwt import (
    IDENTITY_CLAIM_KEY,
    USER_CLAIMS_KEY,
    AUTH_STAGE,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client

logger = logging.getLogger(__name__)


class AuthMethod:
    JWT = "Bearer"
    HAWK_TOKEN = "Hawk"

    @staticmethod
    def valid_methods():
        methods = []
        for attr in AuthMethod.__dict__:
            value = getattr(AuthMethod, attr)
            if not callable(value) and not attr.startswith("__"):
                methods.append(value)
        return methods


def check_token_valid_for_mfa(token):
    auth_stage = token[USER_CLAIMS_KEY].get(AUTH_STAGE)
    if auth_stage != AuthStage.SECOND:
        raise AccessTokenNotValidForMultiFactorAuthException


def mfa_check(client: Client, user: AuthUser, decoded_token: dict):
    is_client_auth_mfa = client.authType == Client.AuthType.MFA
    if is_client_auth_mfa or user.mfaEnabled:
        check_token_valid_for_mfa(decoded_token)


def get_auth_user(user_id: str) -> AuthUser:
    set_user({SentryAdapter.USER_ID: user_id})
    auth_repo = inject.instance(AuthRepository)
    auth_user = auth_repo.get_user(uid=user_id)
    if not auth_user:
        logger.warning(f"An identity {user_id} without user in db tried to access")
        raise DetailedException(InvalidRequestException, "Unauthorised User", 401)
    if auth_user.status != AuthUser.Status.NORMAL:
        raise UnauthorizedException
    return auth_user


def get_authorization_method_type(header_name: str = "Authorization") -> AuthMethod:
    authorization_header = request.headers.get(header_name)
    if not authorization_header:
        raise NoAuthorizationError
    method = authorization_header.split()[0]
    if method not in AuthMethod.valid_methods():
        raise UnauthorizedException
    return method


def check_auth(extract_auth_user=True, extract_extras=True):
    auth_type = get_authorization_method_type()
    auth_user = None
    if auth_type == AuthMethod.JWT:
        try:
            decoded_token = verify_jwt_in_request()
        except InvalidHeaderError as e:
            raise WrongTokenException(message=str(e))

        uid = decoded_token[IDENTITY_CLAIM_KEY]
        server_config = inject.instance(PhoenixServerConfig)
        project_id = decoded_token[USER_CLAIMS_KEY]["projectId"]
        client_id = decoded_token[USER_CLAIMS_KEY]["clientId"]
        check_project(server_config.server.project, project_id)
        client: Client = get_client(server_config.server.project, client_id)
        auth_user = get_auth_user(uid)
        check_token_issued_after_password_update(auth_user, decoded_token.get("iat"))
        if extract_auth_user:
            mfa_check(client, auth_user, decoded_token)
    elif auth_type == AuthMethod.HAWK_TOKEN:
        receiver: mohawk.Receiver = get_hawk_receiver()
        user_key = UserKey.from_string(receiver.parsed_header["id"])
        auth_user = get_auth_user(user_key.userId)

    if extract_auth_user:
        g.auth_user = auth_user
        if extract_extras:
            event_bus = inject.instance(EventBusAdapter)
            event = TokenExtractionEvent.from_dict(
                auth_user.to_dict(include_none=False)
            )
            event_bus.emit(event, raise_error=True)


def auth_required():
    def decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            extract_auth_user = kwargs.pop("extract_auth_user", True)
            extract_extras = kwargs.pop("extract_extra", True)
            check_auth(extract_auth_user, extract_extras)

            return func(*args, **kwargs)

        return _wrapper

    return decorator
