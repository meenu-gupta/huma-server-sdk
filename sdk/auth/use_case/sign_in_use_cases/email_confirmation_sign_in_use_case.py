from sdk.auth.enums import Method
from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import ConfirmationRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.auth.use_case.utils import build_user_claims
from sdk.common.exceptions.exceptions import EmailNotVerifiedException


class EmailConfirmationSignInUseCase(BaseSignInMethodUseCase):
    def _get_user(self, request_object: ConfirmationRequestObject):
        return get_user(self._auth_repo, email=request_object.email)

    def _validate(self, user: AuthUser, request_object: ConfirmationRequestObject):
        if not user.emailVerified:
            raise EmailNotVerifiedException

    @staticmethod
    def _prepare_refresh_token_claims(request_object: ConfirmationRequestObject):
        return build_user_claims(
            request_object.projectId,
            request_object.clientId,
            provider=Method.EMAIL_PASSWORD,
        )
