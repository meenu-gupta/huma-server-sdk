import datetime

from sdk.auth.enums import AuthStage
from sdk.auth.events.post_sign_in_event import PostSignInEvent
from sdk.auth.helpers.session_helpers import register_session
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.auth_response_objects import SignInResponseObject
from sdk.auth.use_case.utils import (
    build_user_claims,
    check_if_password_expired,
    get_token_expires_in,
    get_client,
)
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.token.jwt.jwt import USER_CLAIMS_KEY
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client


class BaseSignInMethodUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        auth_repo: AuthRepository,
        config: PhoenixServerConfig,
        token_adapter: TokenAdapter,
        email_verification_adapter: EmailVerificationAdapter,
        event_bus: EventBusAdapter,
    ):
        self._token_adapter = token_adapter
        self._auth_repo = auth_repo
        self._event_bus = event_bus
        self._config = config
        self._email_verify_adapter = email_verification_adapter

    def _get_user(self, request_object: SignInRequestObject):
        raise NotImplementedError

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
        raise NotImplementedError

    @staticmethod
    def _prepare_refresh_token_claims(request_object: SignInRequestObject):
        return build_user_claims(
            request_object.projectId,
            request_object.clientId,
            provider=request_object.method,
            auth_stage=AuthStage.NORMAL,
        )

    def _prepare_refresh_token(self, user: AuthUser, user_claims: dict, client: Client):
        expires_delta = None

        if client.refreshTokenExpiresAfterMinutes:
            expires_delta = datetime.timedelta(
                minutes=client.refreshTokenExpiresAfterMinutes
            )

        return self._token_adapter.create_refresh_token(
            identity=user.id, user_claims=user_claims, expires_delta=expires_delta
        )

    def _prepare_auth_token_claims(self, refresh_token: str):
        decoded_ref_token = self._token_adapter.verify_token(
            refresh_token, request_type="refresh"
        )
        claims = decoded_ref_token[USER_CLAIMS_KEY]
        return claims

    def _prepare_auth_token(self, user: AuthUser, user_claims: dict, client: Client):
        expires_delta = datetime.timedelta(
            minutes=client.accessTokenExpiresAfterMinutes
        )
        auth_token = self._token_adapter.create_access_token(
            identity=user.id, user_claims=user_claims, expires_delta=expires_delta
        )
        return auth_token

    def _session_action(
        self, user: AuthUser, request_object: SignInRequestObject, refresh_token: str
    ):
        register_session(
            user.id, request_object.deviceAgent, refresh_token, self._auth_repo
        )

    def _prepare_response(self, user: AuthUser, refresh_token: str, auth_token: str):
        ref_expires_in = get_token_expires_in(
            refresh_token, "refresh", self._token_adapter
        )
        auth_token_expires_in = get_token_expires_in(
            auth_token, "access", self._token_adapter
        )
        return SignInResponseObject(
            refresh_token=refresh_token,
            uid=user.id,
            expires_in=ref_expires_in,
            auth_token=auth_token,
            auth_token_expires_in=auth_token_expires_in,
        )

    def _post_sign_in_auth(
        self, request_object: SignInRequestObject, user: AuthUser, client: Client
    ):
        check_if_password_expired(user, client)
        callback_data = request_object.to_dict(include_none=False)
        callback_data.update({"user_id": user.id})
        event = PostSignInEvent.from_dict(callback_data)
        self._event_bus.emit(event, raise_error=True)

    def process_request(
        self, request_object: SignInRequestObject
    ) -> SignInResponseObject:
        client = get_client(self._config.server.project, request_object.clientId)
        user = self._get_user(request_object)
        self._validate(user, request_object)

        refresh_token = self._retrieve_refresh_token(user, request_object, client)

        auth_token_claims = self._prepare_auth_token_claims(refresh_token)
        auth_token = self._prepare_auth_token(user, auth_token_claims, client)
        self._post_sign_in_auth(request_object, user, client)
        self._session_action(user, request_object, refresh_token)
        return self._prepare_response(user, refresh_token, auth_token)

    def _retrieve_refresh_token(self, user, request_object, client):
        refresh_token_user_claims = self._prepare_refresh_token_claims(request_object)
        refresh_token = self._prepare_refresh_token(
            user, refresh_token_user_claims, client
        )
        return refresh_token
