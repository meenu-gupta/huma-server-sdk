import datetime

from sdk.auth.enums import Method, AuthStage
from sdk.auth.helpers.session_helpers import update_current_session_v1
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.use_case.utils import get_token_expires_in

from sdk.common.exceptions.exceptions import (
    InvalidTokenProviderException,
    WrongTokenException,
    EmailNotVerifiedException,
    PasswordNotSetException,
    InvalidUsernameOrPasswordException,
)
from sdk.common.utils.token.jwt.jwt import (
    IDENTITY_CLAIM_KEY,
    USER_CLAIMS_KEY,
    AUTH_STAGE,
)


class RememberMeSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: SignInRequestObject):
        return get_user(self._auth_repo, email=request_object.email)

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
        self._validate_email_and_password(user, request_object)
        self._validate_token(user, request_object)

    def _validate_email_and_password(
        self, user: AuthUser, request_object: SignInRequestObject
    ):
        # checking if email verified
        if not user.emailVerified:
            raise EmailNotVerifiedException
        # checking password set
        if not user.hashedPassword:
            raise PasswordNotSetException
        # checking if password is valid
        password_valid = self._auth_repo.validate_password(
            password=request_object.password, uid=user.id
        )
        if not password_valid:
            raise InvalidUsernameOrPasswordException

    def _validate_token(self, user: AuthUser, request_object: SignInRequestObject):
        decoded_sfa_ref_token = self._token_adapter.verify_token(
            request_object.refreshToken, request_type="refresh"
        )
        provider = decoded_sfa_ref_token[USER_CLAIMS_KEY]["method"]
        if provider != Method.TWO_FACTOR_AUTH:
            raise InvalidTokenProviderException(
                "Remember me flow requires a second-factor token"
            )

        uid = decoded_sfa_ref_token[IDENTITY_CLAIM_KEY]
        ref_auth_stage = decoded_sfa_ref_token[USER_CLAIMS_KEY][AUTH_STAGE]
        if uid != user.id or ref_auth_stage != AuthStage.SECOND:
            raise WrongTokenException

    def _session_action(
        self, user: AuthUser, request_object: SignInRequestObject, refresh_token: str
    ):
        update_current_session_v1(
            user.id,
            request_object.deviceAgent,
            self._auth_repo,
            request_object.refreshToken,
            refresh_token,
        )

    def _retrieve_refresh_token(self, user, request_object, client):
        refresh_token_user_claims = self._prepare_refresh_token_claims(request_object)

        ref_token_expires_in = get_token_expires_in(
            request_object.refreshToken, "refresh", self._token_adapter
        )
        refresh_token = self.prepare_mfa_refresh_token(
            ref_token_expires_in, user.id, refresh_token_user_claims
        )
        return refresh_token

    @staticmethod
    def _prepare_refresh_token_claims(request_object: SignInRequestObject):
        claims = BaseSignInMethodUseCase._prepare_refresh_token_claims(request_object)
        claims[AUTH_STAGE] = AuthStage.SECOND
        return claims

    def prepare_mfa_refresh_token(self, expires_in, user_id, user_claims):
        if expires_in:
            expires_delta = datetime.timedelta(seconds=expires_in)
        else:
            expires_delta = None
        refresh_token = self._token_adapter.create_refresh_token(
            identity=user_id,
            user_claims=user_claims,
            expires_delta=expires_delta,
        )
        return refresh_token
