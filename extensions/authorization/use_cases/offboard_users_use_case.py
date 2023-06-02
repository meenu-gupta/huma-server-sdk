from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.events.post_user_off_board_event import (
    PostUserOffBoardEvent,
)
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    OffBoardUsersRequestObject,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    UserAlreadyOffboardedException,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values
from sdk.common.utils.convertible import ConvertibleClassValidationError


class OffBoardUsersUseCase(UseCase):
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

    def process_request(self, request_object: OffBoardUsersRequestObject) -> Response:
        user_ids = list(set(request_object.userIds))
        self._validate_user_ids_for_offboarding(
            user_ids=user_ids, deployment_id=request_object.deployment.id
        )
        self._validate_offboarding_reason()
        status_data = {
            BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED,
            BoardingStatus.SUBMITTER_ID: request_object.submitterId,
            BoardingStatus.DETAILS_OFF_BOARDED: request_object.detailsOffBoarded,
            BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED,
        }
        status_data = remove_none_values(status_data)
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
        self._post_off_board(user_ids=user_ids, detail=request_object.detailsOffBoarded)
        return Response({"offboardedUsers": len(user_ids)})

    def _validate_user_ids_for_offboarding(
        self, user_ids: list[str], deployment_id: str
    ):
        users = self._repo.retrieve_simple_user_profiles_by_ids(ids=user_ids)

        for auth_user in map(lambda x: AuthorizedUser(x, deployment_id), users):
            if auth_user.deployment_id() != deployment_id:
                msg = f"User #{auth_user.id} does not exist in deployment #{deployment_id}."
                raise ConvertibleClassValidationError(msg)

        for user in users:
            if user.is_off_boarded():
                raise UserAlreadyOffboardedException

    def _validate_offboarding_reason(self):
        offboarding_reasons = self.request_object.deployment.features.offBoardingReasons
        reasons_names = {reason.displayName for reason in offboarding_reasons.reasons}
        if (
            not offboarding_reasons.otherReason
            and self.request_object.detailsOffBoarded not in reasons_names
        ):
            raise InvalidRequestException("Invalid details off boarded")

    def _post_off_board(self, user_ids: list[str], detail: str):
        for user_id in user_ids:
            self._event_bus.emit(PostUserOffBoardEvent(user_id, detail))
