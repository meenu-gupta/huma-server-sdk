from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.model.auth_user import AuthUser, AuthIdentifierType
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.auth_use_cases import validate_phone_number_code
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)


class PhoneNumberSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: SignInRequestObject):
        return get_user(self._auth_repo, phone_number=request_object.phoneNumber)

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
        validate_phone_number_code(
            self._config, user.phoneNumber, request_object.confirmationCode
        )
        self.verify_phone_number(user)

    def verify_phone_number(self, user: AuthUser):
        if user.has_mfa_identifier_verified(AuthIdentifierType.PHONE_NUMBER):
            return
        user.remove_mfa_identifier(AuthIdentifierType.PHONE_NUMBER)
        user.add_mfa_identifier(AuthIdentifierType.PHONE_NUMBER, user.phoneNumber, True)
        mfa_identifiers = user.to_dict()[AuthUser.MFA_IDENTIFIERS]
        self._auth_repo.set_auth_attributes(user.id, mfa_identifiers=mfa_identifiers)
