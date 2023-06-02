import datetime

import pytz

from sdk.auth.enums import AuthStage, Method
from sdk.auth.model.auth_user import AuthUser, AuthIdentifierType
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.validators import validate_project_id
from sdk.common.adapter.sms_adapter_factory import SMSAdapterFactory
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.exceptions.exceptions import (
    TokenExpiredException,
    PasswordExpiredException,
    DetailedException,
    ErrorCodes,
    EmailNotSetException,
    EmailNotVerifiedException,
    PhoneNumberNotSetException,
    PhoneNumberNotVerifiedException,
    PasswordNotSetException,
    InvalidVerificationCodeException,
)
from sdk.common.utils.token.jwt.jwt import AUTH_STAGE, USER_CLAIMS_KEY
from sdk.phoenix.config.server_config import Project, Client, PhoenixServerConfig


PACIFIER_EMAIL = "apple@huma.com"
PACIFIER_CONFIRMATION_CODE = "202020"

TEST_PHONE_NUMBER = "+441700000000"
TEST_CONFIRMATION_CODE = "010101"


def build_user_claims(
    project_id: str,
    client_id: str,
    provider: Method,
    auth_stage: int = AuthStage.NORMAL.value,
):
    return {
        "projectId": project_id,
        "clientId": client_id,
        "method": provider,
        AUTH_STAGE: auth_stage,
    }


def check_project(project: Project, project_id: str):
    validate_project_id(project_id, project)


def check_token_issued_after_password_update(auth_user: AuthUser, token_issued_at):
    """If password was updated, we consider token as invalid"""
    is_initial_password = (
        auth_user.passwordUpdateDateTime == auth_user.passwordCreateDateTime
    )
    if not auth_user.passwordUpdateDateTime or is_initial_password:
        return
    token_issued_at_datetime = datetime.datetime.fromtimestamp(
        token_issued_at, pytz.UTC
    )
    # removing microseconds because "issued at" timestamp has no microseconds
    updated_at = auth_user.passwordUpdateDateTime.replace(microsecond=0)
    if not updated_at.tzinfo:
        updated_at = updated_at.replace(tzinfo=pytz.UTC)
    if updated_at > token_issued_at_datetime:
        raise TokenExpiredException


def check_if_password_expired(user: AuthUser, client: Client):
    if user.passwordUpdateDateTime:
        expiration_days = client.passwordExpiresIn
        expiration_date = user.passwordUpdateDateTime + datetime.timedelta(
            days=expiration_days
        )
        if datetime.datetime.utcnow() > expiration_date:
            raise PasswordExpiredException


def get_client(project: Project, client_id: str):
    client = project.get_client_by_id(client_id)
    if client is None:
        raise DetailedException(
            ErrorCodes.INVALID_CLIENT_ID,
            debug_message="Invalid client id",
            status_code=400,
        )

    return client


def is_second_auth_stage(decoded_ref_token):
    stage = decoded_ref_token[USER_CLAIMS_KEY].get(AUTH_STAGE)
    if stage:
        return stage == AuthStage.SECOND
    # old logic, will be deprecated soon
    method = decoded_ref_token[USER_CLAIMS_KEY].get("method")
    return method == Method.TWO_FACTOR_AUTH


def check_tfa_requirements_met(user):
    # checking if email set
    if not user.email:
        raise EmailNotSetException
    # checking if email verified
    if not user.emailVerified:
        raise EmailNotVerifiedException
    # checking phone number set
    if not user.has_mfa_identifier(AuthIdentifierType.PHONE_NUMBER):
        raise PhoneNumberNotSetException
    # checking if phoneNumber verified
    if not user.has_mfa_identifier_verified(AuthIdentifierType.PHONE_NUMBER):
        raise PhoneNumberNotVerifiedException
    # checking password set
    if not user.hashedPassword:
        raise PasswordNotSetException


def get_token_expires_in(token: str, token_type: str, token_adapter: TokenAdapter):
    decoded_ref_token = token_adapter.verify_token(token, request_type=token_type)
    expires_in = None
    if "exp" in decoded_ref_token:
        expires_at = datetime.datetime.utcfromtimestamp(decoded_ref_token["exp"])
        expires_in = (expires_at - datetime.datetime.utcnow()).total_seconds()
    return expires_in


def verify_mfa_identifier(
    user: AuthUser, identifier_type: AuthIdentifierType, auth_repo: AuthRepository
):
    # NOTE: assuming each type of identifier is unique
    updated_identifiers = []
    for identifier in user.mfaIdentifiers:
        if identifier.type == identifier_type:
            identifier.verified = True
        updated_identifiers.append(identifier.to_dict())
    auth_repo.set_auth_attributes(user.id, mfa_identifiers=updated_identifiers)


def mask_phone_number(phone_number: str):
    public_part = phone_number[-3:]
    masked_part = ["*" for _ in phone_number[:-3]]
    return "".join(masked_part) + public_part


def is_test_phone_number(phone_number: str, config: PhoenixServerConfig):
    return config.server.testEnvironment and phone_number == TEST_PHONE_NUMBER


def validate_phone_number_code(
    server_config: PhoenixServerConfig, phone_number: str, code: str
):
    if is_test_phone_number(phone_number, server_config):
        return code == TEST_CONFIRMATION_CODE

    sms_verification_adapter = SMSAdapterFactory.get_sms_adapter(
        server_config.server.adapters, phone_number
    )
    code_valid = sms_verification_adapter.verify_code(code, phone_number)
    if not code_valid:
        raise InvalidVerificationCodeException
