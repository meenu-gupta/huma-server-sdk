from extensions.authorization.events import PostUserReactivationEvent
from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, BoardingStatus
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    ReactivateUserRequestObject,
)
from extensions.exceptions import UserWithdrewEconsent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import UserAlreadyActiveException
from sdk.common.utils import inject
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.phoenix.audit_logger import AuditLog


class ReactivateUserUseCase(UseCase):
    user = None

    @inject.autoparams()
    def __init__(self, auth_repo: AuthorizationRepository, event_bus: EventBusAdapter):
        self._repo = auth_repo
        self._event_bus = event_bus

    def process_request(self, request_object: ReactivateUserRequestObject):
        user = self._repo.retrieve_simple_user_profile(user_id=request_object.userId)
        self._validate_user_off_boarded_or_raise_error(user)
        user_id = self._reactivate_user(request_object.userId)
        self._reactivate_proxies_for_users(user)
        return Response(value=user_id)

    def _reactivate_proxies_for_users(self, user: User):
        auth_user = AuthorizedUser(user)
        for proxy in auth_user.get_assigned_proxies(to_dict=False) or []:
            if not proxy.is_off_boarded():
                continue
            self._reactivate_user(proxy.id)
            self._create_audit_log_for_reactivated_proxy(proxy.id)

    def _reactivate_user(self, user_id: str):
        reactivation_info = self._build_reactivation_info(user_id)
        user_id = self._repo.update_user_profile(reactivation_info)
        self._event_bus.emit(PostUserReactivationEvent(user_id))
        return user_id

    def _build_reactivation_info(self, user_id: str) -> User:
        boarding_status = {
            BoardingStatus.STATUS: BoardingStatus.Status.ACTIVE,
            BoardingStatus.SUBMITTER_ID: self.request_object.submitterId,
        }
        return User.from_dict({User.ID: user_id, User.BOARDING_STATUS: boarding_status})

    @staticmethod
    def _validate_user_off_boarded_or_raise_error(user: User):
        if not user.is_off_boarded():
            raise UserAlreadyActiveException
        if (
            user.boardingStatus.reasonOffBoarded
            == BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF.value
        ):
            raise UserWithdrewEconsent

    @staticmethod
    def _create_audit_log_for_reactivated_proxy(proxy_id: str):
        AuditLog.create_log(
            action=AuthorizationAction.ReactivateUser, user_id=proxy_id, secure=True
        )
