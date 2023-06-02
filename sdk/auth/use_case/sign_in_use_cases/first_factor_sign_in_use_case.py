from sdk.auth.enums import AuthStage
from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.common.exceptions.exceptions import (
    EmailNotVerifiedException,
    PasswordNotSetException,
    InvalidUsernameOrPasswordException,
)
from sdk.common.utils.token.jwt.jwt import AUTH_STAGE


class TFAFirstFactorSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: SignInRequestObject):
        return get_user(self._auth_repo, email=request_object.email)

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
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

    @staticmethod
    def _prepare_refresh_token_claims(request_object: SignInRequestObject):
        claims = BaseSignInMethodUseCase._prepare_refresh_token_claims(request_object)
        claims[AUTH_STAGE] = AuthStage.FIRST
        return claims
