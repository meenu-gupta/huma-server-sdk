from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.events.post_user_reactivation_event import (
    PostUserReactivationEvent,
)
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    ReactivateUsersRequestObject,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.exceptions import UserWithdrewEconsent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import UserAlreadyActiveException
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.audit_logger import AuditLog


class ReactivateUsersUseCase(UseCase):
    @inject.autoparams()
    def __init__(
        self,
        auth_repo: AuthorizationRepository,
        deployment_repo: DeploymentRepository,
        event_bus: EventBusAdapter,
    ):
        self._repo = auth_repo
        self._event_bus = event_bus
        self.deployment_repo = deployment_repo

    def process_request(self, request_object: ReactivateUsersRequestObject) -> Response:
        user_ids = list(set(request_object.userIds))
        proxy_user_ids = self._validate_users_and_find_proxies(
            user_ids=user_ids, deployment_id=request_object.deploymentId
        )
        user_ids.extend(proxy_user_ids)
        status_data = {
            BoardingStatus.STATUS: BoardingStatus.Status.ACTIVE,
            BoardingStatus.SUBMITTER_ID: request_object.submitterId,
        }
        users = [
            User.from_dict(
                {
                    User.ID: user_id,
                    User.BOARDING_STATUS: status_data,
                }
            )
            for user_id in user_ids
        ]

        self._repo.update_user_profiles(users)
        for proxy_id in proxy_user_ids:
            self._create_audit_log_for_reactivated_proxy(proxy_id=proxy_id)
        self._post_reactivation(user_ids=user_ids)
        return Response({"reactivatedUsers": len(user_ids)})

    def _validate_users_and_find_proxies(self, user_ids: list[str], deployment_id: str):
        users = self._repo.retrieve_simple_user_profiles_by_ids(ids=user_ids)

        for user in users:
            if not user.is_off_boarded():
                raise UserAlreadyActiveException

            if (
                user.boardingStatus.reasonOffBoarded
                == BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF.value
            ):
                raise UserWithdrewEconsent

        proxy_user_ids = []
        for auth_user in map(lambda x: AuthorizedUser(x, deployment_id), users):
            if auth_user.deployment_id() != deployment_id:
                msg = f"User #{auth_user.id} does not exist in deployment #{deployment_id}."
                raise ConvertibleClassValidationError(msg)
            proxies = auth_user.get_assigned_proxies(to_dict=False) or []
            offboarded_proxies = [
                proxy.id for proxy in proxies if proxy.is_off_boarded()
            ]
            proxy_user_ids.extend(offboarded_proxies)
        return proxy_user_ids

    @staticmethod
    def _create_audit_log_for_reactivated_proxy(proxy_id: str):
        AuditLog.create_log(
            action=AuthorizationAction.ReactivateUsers, user_id=proxy_id, secure=True
        )

    def _post_reactivation(self, user_ids: list[str]):
        for user_id in user_ids:
            self._event_bus.emit(PostUserReactivationEvent(user_id))
