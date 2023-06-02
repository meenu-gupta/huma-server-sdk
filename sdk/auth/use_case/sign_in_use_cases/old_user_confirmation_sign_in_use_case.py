from sdk.auth.enums import Method, AuthStage
from sdk.auth.helpers.auth_helpers import get_user
from sdk.auth.model.auth_user import AuthUser
from sdk.auth.use_case.auth_request_objects import ConfirmationRequestObject
from sdk.auth.use_case.sign_in_use_cases.base_sign_in_method_use_case import (
    BaseSignInMethodUseCase,
)
from sdk.auth.use_case.utils import build_user_claims, check_tfa_requirements_met
from sdk.common.exceptions.exceptions import InvalidRequestException


class TFAOldUserConfirmationSignInUseCase(BaseSignInMethodUseCase):
    """
    Used for cases when we need to sign in old user which confirmed phone number
    to make sign in without need to pass the 2FA flow.
    """

    def _get_user(self, request_object: ConfirmationRequestObject):
        if request_object.phoneNumber and request_object.email:
            return get_user(self._auth_repo, email=request_object.email)
        elif request_object.email:
            return get_user(self._auth_repo, email=request_object.email)
        else:
            raise InvalidRequestException

    def _validate(self, user: AuthUser, request_object: ConfirmationRequestObject):
        check_tfa_requirements_met(user)

    @staticmethod
    def _prepare_refresh_token_claims(request_object: ConfirmationRequestObject):
        return build_user_claims(
            request_object.projectId,
            request_object.clientId,
            provider=Method.TWO_FACTOR_AUTH,
            auth_stage=AuthStage.SECOND,
        )
