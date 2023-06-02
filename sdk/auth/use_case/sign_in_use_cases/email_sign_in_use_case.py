from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import SignInRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.auth.use_case.utils import PACIFIER_EMAIL, PACIFIER_CONFIRMATION_CODE
from sdk.common.exceptions.exceptions import InvalidVerificationCodeException


class EmailSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: SignInRequestObject):
        return get_user(self._auth_repo, email=request_object.email)

    def _validate(self, user: AuthUser, request_object: SignInRequestObject):
        pacifier_email = request_object.email == PACIFIER_EMAIL
        pacifier_code = request_object.confirmationCode == PACIFIER_CONFIRMATION_CODE
        # WARN hacking for appstore
        if pacifier_email and pacifier_code:
            return

        valid = self._email_verify_adapter.verify_code(
            code=request_object.confirmationCode, email=request_object.email
        )
        if not valid:
            raise InvalidVerificationCodeException
        # confirming email
        self._auth_repo.confirm_email(email=request_object.email, uid=user.id)
