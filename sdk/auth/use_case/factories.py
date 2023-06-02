from sdk.auth.enums import Method, AuthStage
from sdk.auth.use_case.sign_in_use_cases.email_password_sign_in_use_case import (
    EmailPasswordSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.email_sign_in_use_case import (
    EmailSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.first_factor_sign_in_use_case import (
    TFAFirstFactorSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.phone_number_sign_in_use_case import (
    PhoneNumberSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.remember_me_sign_in_use_case import (
    RememberMeSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.second_factor_sign_in_use_case import (
    TFASecondFactorSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.second_factor_sign_in_use_case_v1 import (
    TFASecondFactorSignInUseCaseV1,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


def sign_in_use_case_factory(method: Method, auth_stage: AuthStage):
    if method is Method.PHONE_NUMBER:
        use_case = PhoneNumberSignInUseCase()

    elif method is Method.EMAIL:
        use_case = EmailSignInUseCase()

    elif method is Method.EMAIL_PASSWORD:
        use_case = EmailPasswordSignInUseCase()

    elif method is Method.TWO_FACTOR_AUTH:
        if auth_stage is AuthStage.FIRST:
            use_case = TFAFirstFactorSignInUseCase()
        elif auth_stage is AuthStage.SECOND:
            use_case = TFASecondFactorSignInUseCase()
        else:
            raise InvalidRequestException("Invalid sign in method")
    else:
        raise InvalidRequestException("Invalid sign in method")
    return use_case


def sign_in_use_case_factory_v1(method: Method, auth_stage: AuthStage):
    if method is Method.PHONE_NUMBER:
        use_case = PhoneNumberSignInUseCase()

    elif method is Method.EMAIL:
        use_case = EmailSignInUseCase()

    elif method is Method.EMAIL_PASSWORD:
        use_case = EmailPasswordSignInUseCase()

    elif method is Method.TWO_FACTOR_AUTH:
        if auth_stage is AuthStage.FIRST:
            use_case = TFAFirstFactorSignInUseCase()
        elif auth_stage is AuthStage.SECOND:
            use_case = TFASecondFactorSignInUseCaseV1()
        elif auth_stage is AuthStage.REMEMBER_ME:
            use_case = RememberMeSignInUseCase()
        else:
            raise InvalidRequestException("Invalid sign in method")
    else:
        raise InvalidRequestException("Invalid sign in method")
    return use_case
