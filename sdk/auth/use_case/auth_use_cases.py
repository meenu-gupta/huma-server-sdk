import datetime
import secrets
from abc import ABC
from copy import deepcopy
from typing import Union

import jwt
from jwt import DecodeError
from pymongo.errors import DuplicateKeyError

from sdk.auth.enums import AuthStage, Method
from sdk.auth.events.check_attributes_event import CheckAuthAttributesEvent
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.auth.events.generate_token_event import GenerateTokenEvent
from sdk.auth.events.mfa_required_event import MFARequiredEvent
from sdk.auth.events.post_sign_up_event import PostSignUpEvent
from sdk.auth.events.pre_sign_up_event import PreSignUpEvent
from sdk.auth.events.set_auth_attributes_events import (
    PostSetAuthAttributesEvent,
    PreSetAuthAttributesEvent,
)
from sdk.auth.events.sign_out_event import SignOutEvent, SignOutEventV1
from sdk.auth.helpers.auth_helpers import get_user, update_password
from sdk.auth.helpers.session_helpers import (
    check_session_is_active,
    update_current_session,
    update_current_session_v1,
)
from sdk.auth.model.auth_user import AuthUser, AuthIdentifierType, AuthKey
from sdk.auth.model.session import DeviceSession, DeviceSessionV1
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import (
    SignUpRequestObject,
    SignOutRequestObjectV1,
    AuthProfileRequestObject,
    RefreshTokenRequestObject,
    SendVerificationTokenRequestObject,
    ConfirmationRequestObject,
    SetAuthAttributesRequestObject,
    CheckAuthAttributesRequestObject,
    SendVerificationTokenMethod,
    DeleteUserRequestObject,
    GenerateAuthKeysRequestObject,
    CreateServiceAccountRequestObject,
    RefreshTokenRequestObjectV1,
)
from sdk.auth.use_case.auth_response_objects import (
    SignUpResponseObject,
    AuthProfileResponseObject,
    RefreshTokenResponseObject,
    SignInResponseObject,
    SendVerificationTokenResponseObject,
    ConfirmationResponseObject,
    SetAuthAttributesResponseObject,
    CheckAuthAttributesResponseObject,
    RetrieveDeepLinkAppleAppResponseObject,
    GenerateAuthKeysResponseObject,
)
from sdk.auth.use_case.sign_in_use_cases.email_confirmation_sign_in_use_case import (
    EmailConfirmationSignInUseCase,
)
from sdk.auth.use_case.sign_in_use_cases.old_user_confirmation_sign_in_use_case import (
    TFAOldUserConfirmationSignInUseCase,
)
from sdk.auth.use_case.utils import (
    get_client,
    is_test_phone_number,
    mask_phone_number,
    check_project,
    verify_mfa_identifier,
    validate_phone_number_code,
    get_token_expires_in,
    check_token_issued_after_password_update,
    is_second_auth_stage,
    PACIFIER_EMAIL,
)
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.sms_adapter_factory import SMSAdapterFactory
from sdk.common.adapter.token_adapter import TokenAdapter, TokenType
from sdk.common.exceptions.exceptions import (
    InvalidUsernameOrPasswordException,
    InvalidEmailConfirmationCodeException,
    InvalidRequestException,
    InvalidTokenProviderException,
    EmailAlreadySetException,
    PasswordAlreadySetException,
    PhoneNumberNotSetException,
    UserAlreadyExistsException,
    EmailAlreadyVerifiedException,
    PhoneNumberAlreadyVerifiedException,
    InvalidPasswordException,
    ConfirmationCodeIsMissing,
    PhoneNumberAlreadySetException,
)
from sdk.common.localization.utils import Language
from sdk.common.usecase.request_object import RequestObject
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.hash_utils import hash_new_password, is_correct_password
from sdk.common.utils.inject import autoparams
from sdk.common.utils.token.hawk.hawk import UserKey
from sdk.common.utils.token.jwt.jwt import (
    IDENTITY_CLAIM_KEY,
    USER_CLAIMS_KEY,
    AUTH_STAGE,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client


class SignUpUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        server_config: PhoenixServerConfig,
        event_bus: EventBusAdapter,
        confirmation_adapter: EmailConfirmationAdapter,
    ):
        self._repo = repo
        self._server_config = server_config.server
        self._project = self._server_config.project
        self._event_bus = event_bus
        self._confirmation_adapter = confirmation_adapter

    def process_request(
        self, request_object: SignUpRequestObject
    ) -> SignUpResponseObject:
        self._pre_sign_up(request_object)
        auth_user = request_object.to_auth_user()
        try:
            user_id = self._repo.create_user(auth_user=auth_user)
        except DuplicateKeyError:
            self._repo.cancel_transactions()
            raise UserAlreadyExistsException

        except Exception as error:
            self._repo.cancel_transactions()
            raise error

        self._post_sign_up(request_object, user_id)
        self._repo.commit_transactions()
        return SignUpResponseObject(uid=user_id)

    def _pre_sign_up(self, request_object):
        data = request_object
        event = PreSignUpEvent.from_dict(data.to_dict(include_none=False))
        self._event_bus.emit(event, raise_error=True)

    def _post_sign_up(self, request_object, user_id):
        callback_data = request_object
        callback_data = callback_data.to_dict(include_none=False)
        callback_data.update(
            {PostSignUpEvent.SESSION: self._repo.session, PostSignUpEvent.ID: user_id}
        )
        try:
            event = PostSignUpEvent.from_dict(callback_data)
            self._event_bus.emit(event, raise_error=True)
        except Exception as e:
            self._repo.cancel_transactions()
            raise e


class SendVerificationTokenUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        token_adapter: TokenAdapter,
        config: PhoenixServerConfig,
        email_verify_adapter: EmailVerificationAdapter,
        email_confirmation_adapter: EmailConfirmationAdapter,
    ):
        self._repo = repo
        self._config = config
        self._email_verify_adapter = email_verify_adapter
        self._email_confirmation_adapter = email_confirmation_adapter
        self._token_adapter = token_adapter

    def process_request(
        self, request_object: SendVerificationTokenRequestObject
    ) -> SendVerificationTokenResponseObject:
        username = None
        client: Client = get_client(
            self._config.server.project, request_object.clientId
        )
        if request_object.method == SendVerificationTokenMethod.PHONE_NUMBER:
            if is_test_phone_number(request_object.phoneNumber, self._config):
                return SendVerificationTokenResponseObject()
            self._send_phone_number_verification(
                request_object.language,
                request_object.phoneNumber,
                client.smsRetrieverCode,
            )

        elif request_object.method == SendVerificationTokenMethod.EMAIL:
            if request_object.email == PACIFIER_EMAIL:
                return SendVerificationTokenResponseObject()
            user = self._repo.get_user(email=request_object.email)

            if user.userAttributes:
                username = user.userAttributes.get("givenName")

            self._email_verify_adapter.send_verification_email(
                to=request_object.email,
                locale=request_object.language,
                client=client,
                username=username,
            )
            return SendVerificationTokenResponseObject()
        elif request_object.method in (
            SendVerificationTokenMethod.EMAIL_SIGNUP_CONFIRMATION,
            SendVerificationTokenMethod.EXISTING_USER_EMAIL_CONFIRMATION,
        ):
            user = self._repo.get_user(email=request_object.email)

            if user.userAttributes:
                username = user.userAttributes.get("givenName")

            self._email_confirmation_adapter.send_confirmation_email(
                to=request_object.email,
                locale=request_object.language,
                client=client,
                username=username,
                method=request_object.method,
            )
        elif request_object.method == SendVerificationTokenMethod.TWO_FACTOR_AUTH:
            token_data = self._token_adapter.verify_token(
                request_object.refreshToken, request_type="refresh"
            )
            method = token_data[USER_CLAIMS_KEY]["method"]
            uid = token_data[IDENTITY_CLAIM_KEY]

            if method != Method.TWO_FACTOR_AUTH:
                raise InvalidTokenProviderException

            user = get_user(self._repo, uid=uid)
            self._repo.retrieve_device_session(
                user_id=user.id,
                refresh_token=request_object.refreshToken,
                check_is_active=True,
            )
            phone_number_identifier = user.get_mfa_identifier(
                AuthIdentifierType.PHONE_NUMBER
            )
            if not phone_number_identifier:
                raise PhoneNumberNotSetException
            phone_number = phone_number_identifier.value
            if is_test_phone_number(phone_number, self._config):
                return SendVerificationTokenResponseObject()
            self._send_phone_number_verification(
                request_object.language, phone_number, client.smsRetrieverCode
            )
            masked_phone_number = mask_phone_number(phone_number)
            return SendVerificationTokenResponseObject(to=masked_phone_number)
        else:
            raise NotImplementedError

        return SendVerificationTokenResponseObject()

    def _send_phone_number_verification(
        self, language: str, phone_number: str, sms_retriever_code: str
    ):
        sms_verification_adapter = SMSAdapterFactory.get_sms_adapter(
            self._config.server.adapters, phone_number
        )
        sms_verification_adapter.send_verification_code(
            phone_number=phone_number,
            locale=language or Language.EN,
            sms_retriever_code=sms_retriever_code,
        )


class ConfirmationUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        email_confirmation_adapter: EmailConfirmationAdapter,
        config: PhoenixServerConfig,
        token_adapter: TokenAdapter,
        email_verification_adapter: EmailVerificationAdapter,
    ):
        self._repo = repo
        self._email_confirmation_adapter = email_confirmation_adapter
        self._config = config
        self._token_adapter = token_adapter
        self._email_verification_adapter = email_verification_adapter

    def process_request(
        self, request_object: ConfirmationRequestObject
    ) -> Union[ConfirmationResponseObject, SignInResponseObject]:
        check_project(self._config.server.project, request_object.projectId)
        get_client(self._config.server.project, request_object.clientId)
        if request_object.phoneNumber:
            user = get_user(self._repo, email=request_object.email)
            phone_identifier = user.get_mfa_identifier(AuthIdentifierType.PHONE_NUMBER)
            if not phone_identifier:
                raise PhoneNumberNotSetException
            if phone_identifier.verified:
                raise PhoneNumberAlreadyVerifiedException
            if phone_identifier.value != request_object.phoneNumber:
                raise InvalidRequestException
            validate_phone_number_code(
                self._config,
                request_object.phoneNumber,
                request_object.confirmationCode,
            )
            verify_mfa_identifier(user, AuthIdentifierType.PHONE_NUMBER, self._repo)
        else:
            user = get_user(self._repo, email=request_object.email)
            if user.emailVerified:
                raise EmailAlreadyVerifiedException

            self.validate_email_confirmation_code(
                request_object.email, request_object.confirmationCode
            )
            self._repo.confirm_email(email=request_object.email)

        # in case user is eligible for MFA after confirmation, we sign him in with TFA method
        user = get_user(self._repo, uid=user.id)
        if user.eligible_for_mfa:
            use_case = TFAOldUserConfirmationSignInUseCase()
            return use_case.execute(request_object)
        # signing user in if confirming email
        if request_object.email and not request_object.phoneNumber:
            sign_in_use_case = EmailConfirmationSignInUseCase()
            return sign_in_use_case.execute(request_object)
        return ConfirmationResponseObject()

    def validate_email_confirmation_code(self, email: str, code: str):
        try:
            jwt.get_unverified_header(code)
            adapter = self._email_confirmation_adapter
            valid = adapter.verify_code(
                code, email, code_type=adapter.CONFIRMATION_CODE_TYPE
            )
        except DecodeError:
            valid = self._email_verification_adapter.verify_code(code=code, email=email)

        if not valid:
            raise InvalidEmailConfirmationCodeException


class RefreshTokenUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        config: PhoenixServerConfig,
        token_adapter: TokenAdapter,
    ):
        self._repo = repo
        self._config = config
        self._token_adapter = token_adapter

    def process_request(
        self, request_object: RefreshTokenRequestObject
    ) -> RefreshTokenResponseObject:
        refresh_token = request_object.refreshToken
        ref_token_expires_in = get_token_expires_in(
            refresh_token, "refresh", self._token_adapter
        )
        decoded_ref_token = self._token_adapter.verify_token(refresh_token, "refresh")
        uid = decoded_ref_token[IDENTITY_CLAIM_KEY]
        client: Client = self.get_client(decoded_ref_token)

        user = get_user(self._repo, uid=uid)
        check_token_issued_after_password_update(user, decoded_ref_token.get("iat"))
        expires_delta = datetime.timedelta(
            minutes=client.accessTokenExpiresAfterMinutes
        )
        user_claims = {
            **decoded_ref_token[USER_CLAIMS_KEY],
            AuthUser.EMAIL_VERIFIED: user.emailVerified or False,
        }

        if is_second_auth_stage(decoded_ref_token):
            self.mfa_token_check(decoded_ref_token, request_object, client, user)
            # this row can be removed when old logic for "method" is deprecated
            user_claims[AUTH_STAGE] = AuthStage.SECOND
            refresh_token = self.prepare_mfa_refresh_token(
                ref_token_expires_in, uid, user_claims
            )
            user_claims["validForMFA"] = True

        auth_token = self._token_adapter.create_access_token(
            identity=uid, user_claims=user_claims, expires_delta=expires_delta
        )
        update_current_session(
            user.id, request_object.deviceAgent, self._repo, refresh_token
        )
        return RefreshTokenResponseObject(
            auth_token=auth_token,
            expires_in=int(expires_delta.total_seconds()),
            refresh_token=refresh_token,
            refresh_token_expires_in=ref_token_expires_in,
        )

    def mfa_token_check(self, decoded_ref_token, request_object, client, user):
        if request_object.password and request_object.email:
            # to allow refresh token with password
            password_valid = self._repo.validate_password(
                request_object.password, request_object.email, user.id
            )
            if not password_valid:
                raise InvalidUsernameOrPasswordException
        else:
            # to avoid simply refresh token instead of re auth when session times out
            check_session_is_active(
                decoded_ref_token,
                client.accessTokenExpiresAfterMinutes,
            )

    def prepare_mfa_refresh_token(self, expires_in, user_id, user_claims):
        if expires_in:
            expires_delta = datetime.timedelta(seconds=expires_in)
        else:
            expires_delta = None
        refresh_token = self._token_adapter.create_refresh_token(
            identity=user_id,
            user_claims=user_claims,
            expires_delta=expires_delta,
        )
        return refresh_token

    def get_client(self, decoded_refresh_token) -> Client:
        project_id = decoded_refresh_token[USER_CLAIMS_KEY]["projectId"]
        client_id = decoded_refresh_token[USER_CLAIMS_KEY]["clientId"]
        check_project(self._config.server.project, project_id)
        return get_client(self._config.server.project, client_id)


class RefreshTokenUseCaseV1(RefreshTokenUseCase):
    def process_request(
        self, request_object: RefreshTokenRequestObjectV1
    ) -> RefreshTokenResponseObject:
        initial_token = refresh_token = request_object.refreshToken
        ref_token_expires_in = get_token_expires_in(
            refresh_token, "refresh", self._token_adapter
        )
        decoded_ref_token = self._token_adapter.verify_token(refresh_token, "refresh")
        uid = decoded_ref_token[IDENTITY_CLAIM_KEY]
        client: Client = self.get_client(decoded_ref_token)

        current_session = self._repo.retrieve_device_session(
            user_id=uid, refresh_token=request_object.refreshToken, check_is_active=True
        )

        user = get_user(self._repo, uid=uid)

        check_token_issued_after_password_update(user, decoded_ref_token.get("iat"))
        expires_delta = datetime.timedelta(
            minutes=client.accessTokenExpiresAfterMinutes
        )
        user_claims = {
            **decoded_ref_token[USER_CLAIMS_KEY],
            AuthUser.EMAIL_VERIFIED: user.emailVerified or False,
        }
        if request_object.password:
            # to allow refresh token with password
            password_valid = self._repo.validate_password(
                request_object.password, request_object.email, user.id
            )
            if not password_valid:
                raise InvalidUsernameOrPasswordException
        elif request_object.deviceToken:
            self._repo.validate_device_token(
                device_token=request_object.deviceToken, user_id=user.id
            )

        if is_second_auth_stage(decoded_ref_token):
            self.mfa_token_check(decoded_ref_token, client)
            # this row can be removed when old logic for "method" is deprecated
            user_claims[AUTH_STAGE] = AuthStage.SECOND
            # to avoid session updates for when device token present
            if not request_object.deviceToken:
                refresh_token = self.prepare_mfa_refresh_token(
                    ref_token_expires_in, uid, user_claims
                )
                update_current_session_v1(
                    user.id,
                    current_session.deviceAgent,
                    self._repo,
                    initial_token,
                    refresh_token,
                )
            user_claims["validForMFA"] = True

        auth_token = self._token_adapter.create_access_token(
            identity=uid, user_claims=user_claims, expires_delta=expires_delta
        )
        return RefreshTokenResponseObject(
            auth_token=auth_token,
            expires_in=int(expires_delta.total_seconds()),
            refresh_token=refresh_token,
            refresh_token_expires_in=ref_token_expires_in,
        )

    def mfa_token_check(self, decoded_ref_token, client):
        has_creds = self.request_object.password or self.request_object.deviceToken
        if self.request_object.email and has_creds:
            return

        # to avoid simply refresh token instead of re auth when session times out
        check_session_is_active(
            decoded_ref_token, client.accessTokenExpiresAfterMinutes
        )


class AuthAttributesUseCase(UseCase, ABC):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        token_adapter: TokenAdapter,
        event_bus: EventBusAdapter,
        config: PhoenixServerConfig,
    ):
        self._repo = repo
        self._token_adapter = token_adapter
        self._event_bus = event_bus
        self._config = config

    def get_user_from_token(
        self,
        token: str,
        token_type: TokenType,
    ) -> AuthUser:
        if token_type == TokenType.INVITATION:
            decoded_token = self._token_adapter.verify_invitation_token(token)
            email = decoded_token[IDENTITY_CLAIM_KEY]
            return get_user(self._repo, email=email)

        decoded_token = self._token_adapter.verify_token(
            token, request_type=token_type.string_value
        )
        uid = decoded_token[IDENTITY_CLAIM_KEY]
        user = get_user(self._repo, uid=uid)
        if token_type == TokenType.REFRESH:
            check_token_issued_after_password_update(user, decoded_token.get("iat"))
        return user


class SetAuthAttributesUseCase(AuthAttributesUseCase):
    def process_request(
        self, request_object: SetAuthAttributesRequestObject
    ) -> SetAuthAttributesResponseObject:
        check_project(self._config.server.project, request_object.projectId)
        client: Client = get_client(
            self._config.server.project, request_object.clientId
        )
        user = self.get_user_from_token(
            request_object.authToken, request_object.tokenType
        )

        mfa_phone_number_updated = self.check_and_set_phone_number(
            request_object.phoneNumber, user, request_object.confirmationCode
        )

        mfa_device_token_updated = self.check_and_set_device_token(
            request_object.deviceToken, user
        )
        update_data = {
            "password": self.check_and_set_password(user),
            "email": self.check_and_set_email(request_object.email, user),
            "mfa_enabled": self.check_and_set_mfa(request_object.mfaEnabled, client),
            "mfa_identifiers": user.to_dict()[AuthUser.MFA_IDENTIFIERS],
        }
        update_data = remove_none_values(update_data)
        self.pre_set_attributes_event(user.id, update_data)
        self._repo.set_auth_attributes(user.id, **update_data)
        self.post_set_auth_attributes_event(
            **update_data,
            user_id=user.id,
            old_password=request_object.oldPassword,
            language=request_object.language,
            mfa_phone_number_updated=mfa_phone_number_updated,
            mfa_device_token_updated=mfa_device_token_updated,
        )
        response_data = self.prepare_response_data(user)
        return SetAuthAttributesResponseObject(**response_data)

    def prepare_response_data(self, user: AuthUser):
        response_data = {SetAuthAttributesResponseObject.UID: user.id}
        if self.request_object.oldPassword:
            device_session = self._repo.retrieve_device_session(
                user_id=user.id,
                refresh_token=self.request_object.authToken,
                check_is_active=True,
            )
            response_data["refresh_token"] = self._token_adapter.reissue_refresh_token(
                self.request_object.authToken
            )
            update_current_session_v1(
                user.id,
                device_session.deviceAgent,
                self._repo,
                self.request_object.authToken,
                response_data["refresh_token"],
            )
        return response_data

    def post_set_auth_attributes_event(self, **kwargs):
        event = PostSetAuthAttributesEvent.from_dict(kwargs)
        self._event_bus.emit(event, raise_error=True)

    def pre_set_attributes_event(self, user_id, update_data):
        event = PreSetAuthAttributesEvent(user_id=user_id, **update_data)
        self._event_bus.emit(event)

    def check_and_set_phone_number(
        self, phone_number: str, user: AuthUser, confirmation_code: str = None
    ) -> bool:
        if not phone_number:
            return False

        number_field = AuthIdentifierType.PHONE_NUMBER

        if user.has_mfa_identifier_verified(number_field):
            if not confirmation_code:
                raise ConfirmationCodeIsMissing

            if user.get_mfa_identifier(number_field, phone_number):
                raise PhoneNumberAlreadySetException

            validate_phone_number_code(self._config, phone_number, confirmation_code)
            user.remove_mfa_identifier(number_field)
            user.add_mfa_identifier(number_field, phone_number, True)
            return True

        user.remove_mfa_identifier(number_field)
        user.add_mfa_identifier(number_field, phone_number)
        return False

    @staticmethod
    def check_and_set_device_token(device_token: str, user: AuthUser) -> bool:
        if not device_token:
            return False

        identifier_type = AuthIdentifierType.DEVICE_TOKEN

        if user.get_mfa_identifier(identifier_type, device_token):
            return False

        user.add_mfa_identifier(identifier_type, device_token)
        return True

    def check_and_set_password(self, user: AuthUser):
        if not self.request_object.password:
            return
        if not user.hashedPassword:
            return hash_new_password(self.request_object.password)
        elif not self.request_object.oldPassword:
            raise PasswordAlreadySetException
        elif not is_correct_password(
            user.hashedPassword, self.request_object.oldPassword
        ):
            raise InvalidPasswordException
        else:
            update_password(self.request_object.password, user.email, self._repo)

    @staticmethod
    def check_and_set_email(email: str, user: AuthUser):
        if not email:
            return
        if user.email:
            raise EmailAlreadySetException
        return email

    @staticmethod
    def check_and_set_mfa(mfa_enabled: bool, client: Client):
        if mfa_enabled is None:
            return

        client.check_mfa_status(mfa_enabled)
        return mfa_enabled


class CheckAuthAttributesUseCase(AuthAttributesUseCase):
    def process_request(
        self, request_object: CheckAuthAttributesRequestObject
    ) -> CheckAuthAttributesResponseObject:
        check_project(self._config.server.project, request_object.projectId)
        client: Client = get_client(
            self._config.server.project, request_object.clientId
        )

        response_data = {
            CheckAuthAttributesResponseObject.ELIGIBLE_FOR_MFA: False,
            CheckAuthAttributesResponseObject.PASSWORD_SET: False,
        }

        if request_object.authToken:
            user = self.get_user_from_token(
                request_object.authToken, request_object.tokenType
            )
            email_verified = True if user.emailVerified else False

            mfa_phone_identifier = user.get_mfa_identifier(
                AuthIdentifierType.PHONE_NUMBER
            )
            if not mfa_phone_identifier:
                phone_number_verified = False
                phone_number = None
            else:
                phone_number_verified = mfa_phone_identifier.verified
                phone_number = mfa_phone_identifier.value

            mfa_conditions = self._event_bus.emit(MFARequiredEvent(user.id))
            mfa_conditions.extend([user.mfaEnabled, client.is_mfa_required()])
            response_obj = CheckAuthAttributesResponseObject
            response_data[response_obj.EMAIL_VERIFIED] = email_verified
            response_data[response_obj.PHONE_NUMBER_VERIFIED] = phone_number_verified
            response_data[response_obj.PHONE_NUMBER] = phone_number
            response_data[response_obj.MFA_ENABLED] = any(mfa_conditions)

        elif request_object.email:
            user = get_user(self._repo, email=request_object.email)

        elif request_object.phoneNumber:
            user = get_user(self._repo, phone_number=request_object.phoneNumber)
        else:
            raise InvalidRequestException

        response_data[CheckAuthAttributesResponseObject.EMAIL] = user.email
        if user.eligible_for_mfa:
            response_data[CheckAuthAttributesResponseObject.ELIGIBLE_FOR_MFA] = True
        if user.hashedPassword:
            response_data[CheckAuthAttributesResponseObject.PASSWORD_SET] = True

        self.post_check(request_object, user.id)
        return CheckAuthAttributesResponseObject(**response_data)

    def post_check(self, request_object: CheckAuthAttributesRequestObject, user_id):
        event = CheckAuthAttributesEvent(
            user_id, request_object.clientId, request_object.projectId
        )
        self._event_bus.emit(event, raise_error=True)


class AuthProfileUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository):
        self._repo = repo
        self._config = inject.instance(PhoenixServerConfig)
        self._token_adapter = inject.instance(TokenAdapter)

    def process_request(
        self, request_object: AuthProfileRequestObject
    ) -> AuthProfileResponseObject:
        decoded_token = self._token_adapter.verify_token(
            request_object.authToken, request_type="access"
        )
        uid = decoded_token[IDENTITY_CLAIM_KEY]
        project_id = decoded_token[USER_CLAIMS_KEY]["projectId"]
        client_id = decoded_token[USER_CLAIMS_KEY]["clientId"]
        check_project(self._config.server.project, project_id)
        get_client(self._config.server.project, client_id)
        self._repo.get_user(uid=uid)
        return AuthProfileResponseObject(uid=uid)


class SignOutUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository):
        self._repo = repo
        self._event_bus = inject.instance(EventBusAdapter)

    def process_request(self, request_object):
        session = DeviceSession.from_dict(request_object.to_dict(include_none=False))

        response = self._repo.sign_out_device_session(session)

        self._post_sign_out(request_object)
        return response

    def _post_sign_out(self, request_object):
        callback_data = remove_none_values(request_object.to_dict())
        event = SignOutEvent.from_dict(callback_data)
        self._event_bus.emit(event)


class SignOutUseCaseV1(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository, event_bus_adapter: EventBusAdapter):
        self._repo = repo
        self._event_bus = event_bus_adapter

    def process_request(self, request_object: SignOutRequestObjectV1):
        session = DeviceSessionV1.from_dict(request_object.to_dict(include_none=False))
        response = self._repo.sign_out_device_session_v1(session)

        if request_object.deviceToken:
            self._clear_device_token_from_identifiers(
                user_id=request_object.userId, token=request_object.deviceToken
            )

        self._post_sign_out(request_object)

        return response

    def _post_sign_out(self, request_object):
        event = SignOutEventV1(
            user_id=request_object.userId,
            device_push_id=request_object.devicePushId,
            voip_device_push_id=request_object.voipDevicePushId,
        )
        self._event_bus.emit(event)

    def _clear_device_token_from_identifiers(self, user_id: str, token: str):
        auth_user = get_user(self._repo, uid=user_id)
        auth_user.remove_mfa_identifier(AuthIdentifierType.DEVICE_TOKEN, token)
        self._repo.set_auth_attributes(
            uid=user_id, mfa_identifiers=auth_user.to_dict()[AuthUser.MFA_IDENTIFIERS]
        )


class SessionUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository):
        self._repo = repo

    def process_request(self, user_id):
        return self._repo.retrieve_device_sessions_by_user_id(user_id=user_id)


class DeleteUserCase(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository):
        self._repo = repo
        self._event_bus = inject.instance(EventBusAdapter)

    def process_request(self, request_object: DeleteUserRequestObject):
        user_id = request_object.userId
        try:
            self._repo.delete_user(user_id=user_id)
            event = DeleteUserEvent(session=self._repo.session, user_id=user_id)
            self._event_bus.emit(event, raise_error=True)
        except Exception as error:
            self._repo.cancel_transactions()
            raise error
        else:
            self._repo.commit_transactions()


class RetrieveDeepLinkAppleAppUseCase(UseCase):
    template_dict = {
        "applinks": {"apps": [], "details": [{"appIDs": [], "paths": ["*"]}]}
    }

    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
    ):
        self._config = config

    def process_request(self, _: RequestObject):
        ios_app_ids = [
            app_id
            for client in self._config.server.project.clients
            if client.clientType == Client.ClientType.USER_IOS and client.appIds
            for app_id in client.appIds
        ]
        if ios_app_ids:
            template_dict = deepcopy(self.template_dict)
            template_dict["applinks"]["details"][0]["appIDs"] = ios_app_ids
            return RetrieveDeepLinkAppleAppResponseObject(template_dict)
        raise InvalidRequestException


class RetrieveDeepLinkAndroidAppUseCase(UseCase):
    template_dict = {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "",
            "sha256_cert_fingerprints": [],
        },
    }

    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
    ):
        self._config = config

    def process_request(self, _: RequestObject):
        assets_conf = list()
        for client in self._config.server.project.clients:
            if (
                client.clientType == Client.ClientType.USER_ANDROID
                and client.appIds
                and client.fingerprints
            ):
                assets_conf.extend(zip(client.appIds, client.fingerprints))

        if not assets_conf:
            raise InvalidRequestException

        return [self._fill_template(*conf) for conf in assets_conf]

    def _fill_template(self, name: str, fingerprint: str):
        template_dict = deepcopy(self.template_dict)
        template_dict["target"]["package_name"] = name
        template_dict["target"]["sha256_cert_fingerprints"] = [fingerprint]
        return template_dict


class GenerateAuthTokenUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: AuthRepository, event_bus: EventBusAdapter):
        self._repo = repo
        self._event_bus = event_bus

    def process_request(self, request_object: GenerateAuthKeysRequestObject):
        self._event_bus.emit(GenerateTokenEvent(), raise_error=True)

        auth_key, auth_id = GenerateAuthTokenUseCase.generate_auth_keys()

        self._repo.create_auth_keys(
            user_id=request_object.userId,
            auth_key=auth_key,
            auth_identifier=auth_id,
            auth_type=AuthKey.AuthType.HAWK,
        )

        return GenerateAuthKeysResponseObject(
            auth_id=UserKey(
                userId=request_object.userId, authIdentifier=auth_id
            ).to_string(),
            auth_key=auth_key,
        )

    @staticmethod
    def generate_auth_keys():
        return secrets.token_hex(32), secrets.token_hex(12)


class CreateServiceAccountUseCase(UseCase):
    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        event_bus: EventBusAdapter,
        config: PhoenixServerConfig,
    ):
        self._repo = repo
        self._event_bus = event_bus
        self._config = config

    def process_request(self, request_object: CreateServiceAccountRequestObject):
        auth_user = AuthUser(
            status=AuthUser.Status.NORMAL, email=request_object.get_email()
        )
        auth_user.emailVerified = True

        auth_key, auth_id = GenerateAuthTokenUseCase.generate_auth_keys()
        now = datetime.datetime.utcnow()

        auth_user.authKeys = [
            AuthKey(
                authIdentifier=auth_id,
                authKey=auth_key,
                authType=request_object.authType,
                updateDateTime=now,
                createDateTime=now,
            )
        ]

        project = self._config.server.project
        client = project.get_client_by_client_type(Client.ClientType.SERVICE_ACCOUNT)

        auth_user.id = self._repo.create_user(auth_user=auth_user)
        user_data = auth_user.to_dict(include_none=False)
        try:
            event = PostSignUpEvent.from_dict(
                {
                    **user_data,
                    request_object.VALIDATION_DATA: request_object.validationData,
                    PostSignUpEvent.SESSION: self._repo.session,
                    PostSignUpEvent.CLIENT_ID: client.clientId,
                    PostSignUpEvent.TIMEZONE: request_object.timezone,
                    "resource": request_object.resourceId,
                    "roleId": request_object.roleId,
                }
            )
            self._event_bus.emit(event, raise_error=True)
        except Exception as e:
            self._repo.cancel_transactions()
            raise e

        self._repo.commit_transactions()

        return GenerateAuthKeysResponseObject(
            auth_id=UserKey(userId=auth_user.id, authIdentifier=auth_id).to_string(),
            auth_key=auth_key,
        )
