from sdk.auth.events.set_auth_attributes_events import PreRequestPasswordResetEvent
from sdk.auth.helpers.auth_helpers import update_password
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.use_case.auth_request_objects import (
    RequestPasswordResetRequestObject,
    ResetPasswordRequestObject,
)
from sdk.auth.use_case.auth_response_objects import (
    RequestPasswordResetResponseObject,
    ResetPasswordResponseObject,
)
from sdk.auth.use_case.auth_use_cases import check_project, get_client
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import InvalidEmailConfirmationCodeException
from sdk.common.usecase.request_object import RequestObject
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig, Client


class PasswordResetBaseUseCase(UseCase):
    request_object: RequestObject

    @autoparams()
    def __init__(
        self,
        repo: AuthRepository,
        config: PhoenixServerConfig,
        email_confirmation_adapter: EmailConfirmationAdapter,
        event_bus: EventBusAdapter,
    ):
        self._repo = repo
        self._project = config.server.project
        self._email_confirmation_adapter = email_confirmation_adapter
        self._event_bus = event_bus

    def process_request(self, request_object):
        pass


class RequestPasswordResetUseCase(PasswordResetBaseUseCase):
    request_object: RequestPasswordResetRequestObject

    def process_request(self, _):
        check_project(self._project, self.request_object.projectId)
        client: Client = get_client(self._project, self.request_object.clientId)
        user = self._repo.get_user(email=self.request_object.email)
        self.pre_reset_password_event(user.id)
        self._email_confirmation_adapter.send_reset_password_email(
            to=self.request_object.email,
            locale=self.request_object.language,
            client=client,
        )
        return RequestPasswordResetResponseObject()

    def pre_reset_password_event(self, user_id: str):
        event = PreRequestPasswordResetEvent(
            user_id, self.request_object.clientId, self.request_object.projectId
        )
        self._event_bus.emit(event, raise_error=True)


class ResetPasswordUseCase(PasswordResetBaseUseCase):
    request_object: ResetPasswordRequestObject

    def process_request(self, _):
        email = self.request_object.email
        code = self.request_object.code
        adapter = self._email_confirmation_adapter

        if not adapter.verify_code(
            code, email, adapter.RESET_PASSWORD_CODE_TYPE, delete_code=False
        ):
            raise InvalidEmailConfirmationCodeException
        update_password(self.request_object.newPassword, email, self._repo)
        adapter.delete_code(code, email, adapter.RESET_PASSWORD_CODE_TYPE)
        return ResetPasswordResponseObject()
