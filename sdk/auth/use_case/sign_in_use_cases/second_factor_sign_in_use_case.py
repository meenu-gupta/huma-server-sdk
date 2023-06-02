from sdk.auth.enums import Method, AuthStage
from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.helpers.session_helpers import update_current_session
from sdk.auth.model.auth_user import AuthUser, AuthIdentifierType
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.auth.use_case.utils import (
    check_tfa_requirements_met,
    validate_phone_number_code,
)
from sdk.common.exceptions.exceptions import InvalidTokenProviderException
from sdk.common.utils.token.jwt.jwt import (
    IDENTITY_CLAIM_KEY,
    USER_CLAIMS_KEY,
    AUTH_STAGE,
)


class TFASecondFactorSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: SignInRequestObject):
        decoded_sfa_ref_token = self._token_adapter.verify_token(
            request_object.refreshToken, request_type="refresh"
        )
        uid = decoded_sfa_ref_token[IDENTITY_CLAIM_KEY]
        provider = decoded_sfa_ref_token[USER_CLAIMS_KEY]["method"]
        if provider != Method.TWO_FACTOR_AUTH:
            raise InvalidTokenProviderException

        return get_user(self._auth_repo, uid=uid)

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
        check_tfa_requirements_met(user)
        # checking if code is valid
        phone_number_identifier = user.get_mfa_identifier(
            AuthIdentifierType.PHONE_NUMBER
        )
        phone_number = phone_number_identifier.value
        validate_phone_number_code(
            self._config, phone_number, request_object.confirmationCode
        )

    def _session_action(
        self, user: AuthUser, request_object: SignInRequestObject, refresh_token: str
    ):
        update_current_session(
            user.id, request_object.deviceAgent, self._auth_repo, refresh_token
        )

    @staticmethod
    def _prepare_refresh_token_claims(request_object: SignInRequestObject):
        claims = BaseSignInMethodUseCase._prepare_refresh_token_claims(request_object)
        claims[AUTH_STAGE] = AuthStage.SECOND
        return claims
