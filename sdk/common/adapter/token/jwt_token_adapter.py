import datetime
import logging

from jwt import ExpiredSignatureError, InvalidSignatureError, DecodeError

from sdk.auth.use_case.auth_request_objects import TokenType
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    WrongTokenException,
    InvalidEmailConfirmationCodeException,
    InvitationExpiredException,
    TokenExpiredException,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.token.exceptions import NoAuthorizationError
from sdk.common.utils.token.jwt.jwt import (
    decode_jwt,
    encode_access_token,
    encode_refresh_token,
    encode_confirmation_token,
    encode_custom_token,
    IDENTITY_CLAIM_KEY,
    USER_CLAIMS_KEY,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


class JwtTokenAdapter(TokenAdapter):
    @autoparams()
    def __init__(self, jwt_config: JwtTokenConfig, server_config: PhoenixServerConfig):
        self._jwt_config = jwt_config
        self._server_config = server_config

    def verify_token(
        self,
        token: str,
        request_type: str = TokenType.ACCESS.string_value,
        verify_user_claims=True,
    ):
        errors = []
        decoded_token = None
        try:
            decoded_token = decode_jwt(
                token,
                self._jwt_config.secret,
                self._jwt_config.algorithm,
                audience=self._jwt_config.audience,
            )
        except ExpiredSignatureError:
            raise TokenExpiredException

        except NoAuthorizationError as e:
            errors.append(str(e))

        except (InvalidSignatureError, DecodeError):
            raise WrongTokenException

        if not decoded_token:
            raise NoAuthorizationError(errors[0])

        self.verify_token_type(decoded_token, expected_type=request_type)

        return decoded_token

    def create_access_token(
        self,
        identity: str,
        user_claims: dict = None,
        expires_delta=datetime.timedelta(days=1),
    ) -> str:
        return encode_access_token(
            identity,
            self._jwt_config.secret,
            self._jwt_config.algorithm,
            expires_delta,
            False,
            user_claims,
            audience=self._jwt_config.audience,
        )

    def create_refresh_token(
        self,
        identity: str,
        user_claims: dict = None,
        expires_delta: datetime.timedelta = None,
    ) -> str:
        return encode_refresh_token(
            identity,
            self._jwt_config.secret,
            self._jwt_config.algorithm,
            expires_delta,
            user_claims,
            audience=self._jwt_config.audience,
        )

    def create_confirmation_token(self, identity: str, user_claims: dict = None):
        return encode_confirmation_token(
            identity,
            secret=self._server_config.server.auth.signedUrlSecret,
            algorithm=self._jwt_config.algorithm,
            expires_delta=datetime.timedelta(days=1),
            user_claims=user_claims,
        )

    def verify_confirmation_token(self, token: str):
        try:
            decoded_token = decode_jwt(
                token,
                self._server_config.server.auth.signedUrlSecret,
                algorithm="HS256",
            )
        except ExpiredSignatureError:
            raise InvalidEmailConfirmationCodeException("Confirmation code expired")
        except (InvalidSignatureError, DecodeError):
            raise WrongTokenException
        return decoded_token

    def verify_invitation_token(self, token, allow_expired=False):

        try:
            decoded_token = decode_jwt(
                token,
                self._server_config.server.auth.signedUrlSecret,
                algorithm="HS256",
                allow_expired=allow_expired,
            )
        except ExpiredSignatureError:
            raise InvitationExpiredException
        except (InvalidSignatureError, DecodeError):
            raise WrongTokenException
        self.verify_token_type(
            decoded_token, expected_type=TokenType.INVITATION.string_value
        )
        return decoded_token

    def create_token(
        self,
        identity: str = None,
        token_type: str = None,
        user_claims: dict = None,
        expires_delta=False,
    ):
        return encode_custom_token(
            identity,
            secret=self._server_config.server.auth.signedUrlSecret,
            algorithm="HS256",
            expires_delta=expires_delta,
            token_type=token_type,
            user_claims=user_claims,
        )

    @staticmethod
    def verify_token_type(decoded_token: dict, expected_type: str):
        if decoded_token["type"] != expected_type:
            raise WrongTokenException(
                "Only {} tokens are allowed".format(expected_type)
            )

    def reissue_refresh_token(self, token: str):
        decoded_token = self.verify_token(token, TokenType.REFRESH.string_value)
        expires_delta = None
        if "exp" in decoded_token:
            expires_at = datetime.datetime.utcfromtimestamp(decoded_token["exp"])
            expires_in = (expires_at - datetime.datetime.utcnow()).total_seconds()
            expires_delta = datetime.timedelta(seconds=expires_in)
        return self.create_refresh_token(
            identity=decoded_token[IDENTITY_CLAIM_KEY],
            user_claims=decoded_token[USER_CLAIMS_KEY],
            expires_delta=expires_delta,
        )
