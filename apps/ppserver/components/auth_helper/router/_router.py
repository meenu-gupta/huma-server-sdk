import logging

from flask import Blueprint, render_template, request, url_for, redirect, flash, jsonify

from apps.ppserver.components.auth_helper.router.request_objects import (
    SetStaticOTPRequestObject,
)

from extensions.authorization.use_cases.invitation_use_cases import (
    SendInvitationsUseCase,
)
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
)
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.models.authorized_user import AuthorizedUser

from sdk.auth.model.auth_user import AuthIdentifierType, AuthUser
from sdk.auth.repository.mongo_auth_repository import MongoAuthRepository
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.utils import inject
from sdk.auth.use_case.auth_request_objects import (
    SignUpRequestObject,
    SignInRequestObject,
)

from sdk.auth.use_case.auth_use_cases import SignUpUseCase
from sdk.auth.use_case.factories import sign_in_use_case_factory
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter

from sdk.common.exceptions.exceptions import InvalidRequestException


DEVICE_AGENT = "chrome"
CODE_TYPE = "Verification"

helper_router = Blueprint(
    "qa_helper",
    __name__,
    url_prefix="/helper/qa",
    template_folder="templates",
    static_folder="static",
)

logger = logging.getLogger("QAHelper")


@helper_router.get("/")
def index():
    return render_template("qa-helper.html")


@helper_router.post("/otp")
def set_static_otp():
    request_object = SetStaticOTPRequestObject.from_dict(request.form)
    repo = inject.instance(MongoAuthRepository)
    user = repo.get_user(email=request_object.email)
    user.remove_mfa_identifier(AuthIdentifierType.PHONE_NUMBER)
    user.add_mfa_identifier(AuthIdentifierType.PHONE_NUMBER, "+441700000000", True)
    auth_user_dict = user.to_dict(include_none=False)
    repo.set_auth_attributes(
        user.id, mfa_identifiers=auth_user_dict.get(AuthUser.MFA_IDENTIFIERS)
    )
    msg = f"Static OTP set for user {request_object.email}"
    logger.debug(msg)
    flash(msg)
    return redirect(url_for("qa_helper.index"))


@helper_router.get("/signup")
def sign_up_template():
    return render_template("qa-signup.html")


@helper_router.post("/signup")
def sign_up():
    try:
        body = request.form.to_dict()

        manager_email = body.get("managerEmail")
        auth_repo = inject.instance(AuthRepository)
        auth_user = auth_repo.get_user(email=manager_email)

        authorization_repo = inject.instance(AuthorizationRepository)
        auth_user = authorization_repo.retrieve_simple_user_profile(
            user_id=auth_user.id
        )
        submitter = AuthorizedUser(auth_user)
        deployment_ids = submitter.deployment_ids()
        user_type = submitter.user_type()
        if user_type == "Manager":
            email = body.get("email")
            signup_user_body = {
                "emails": [email],
                "expiresIn": "P7D",
                "roleId": "User",
                "clientId": body.get("clientId", ""),
                "projectId": body.get("projectId", ""),
                "language": "en",
                "deploymentIds": deployment_ids,
                "type": "[Permission] Load Send Patient Invite",
                "submitter": submitter,
            }
            request_object = SendInvitationsRequestObject.from_dict(signup_user_body)
            request_object.check_permission(submitter)
            SendInvitationsUseCase().execute(request_object)

            invitation_repo = inject.instance(InvitationRepository)
            invitation = invitation_repo.retrieve_invitation(email=email)

            body.update(
                {
                    "displayName": f'{email.split("@")[0]}-huma',
                    "validationData": {"invitationCode": invitation.code},
                    "method": int(body.get("method")),
                }
            )
            signup_request = SignUpRequestObject.from_dict(body)
            SignUpUseCase().execute(signup_request)

            flash(f"User Sign up successfully with email: {email}")

            return redirect(url_for("qa_helper.sign_in_template"))
        else:
            flash(f"Manager email is not valid: {manager_email}")
            return render_template("qa-signup.html")

    except Exception as e:
        raise InvalidRequestException(str(e))


@helper_router.get("/signin")
def sign_in_template():
    return render_template("qa-signin.html")


@helper_router.post("/signin")
def sign_in():
    try:
        body = request.form.to_dict()

        confirmation_code = EmailConfirmationAdapter().create_or_retrieve_code_for(
            email=body.get("email"), code_type=CODE_TYPE
        )
        body.update(
            {
                "deviceAgent": DEVICE_AGENT,
                "method": int(body.get("method")),
                "confirmationCode": confirmation_code,
            }
        )
        sign_in_data = SignInRequestObject.from_dict(body)
        use_case = sign_in_use_case_factory(sign_in_data.method, sign_in_data.authStage)
        sign_in_response = use_case.execute(sign_in_data)

        return jsonify(sign_in_response.value.to_dict(include_none=False)), 200

    except Exception as e:
        raise InvalidRequestException(str(e))
