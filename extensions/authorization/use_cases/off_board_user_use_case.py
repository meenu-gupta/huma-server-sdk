from typing import Union

from extensions.authorization.events.post_user_off_board_event import (
    PostUserOffBoardEvent,
)
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    OffBoardUserRequestObject,
    SystemOffBoardUserRequestObject,
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

RequestObject = Union[OffBoardUserRequestObject, SystemOffBoardUserRequestObject]


class OffBoardUserUseCase(UseCase):
    request_object: RequestObject

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

    def process_request(self, request_object: RequestObject) -> Response:
        self._check_if_user_off_boarded_and_raise_error(user_id=request_object.userId)
        if isinstance(request_object, OffBoardUserRequestObject):
            self._check_if_reasons_off_boarded_is_valid()

            status_data = {
                BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED,
                BoardingStatus.SUBMITTER_ID: request_object.submitterId,
                BoardingStatus.DETAILS_OFF_BOARDED: request_object.detailsOffBoarded,
                BoardingStatus.REASON_OFF_BOARDED: BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED,
            }
        elif isinstance(request_object, SystemOffBoardUserRequestObject):
            status_data = {
                BoardingStatus.STATUS: BoardingStatus.Status.OFF_BOARDED,
                BoardingStatus.REASON_OFF_BOARDED: request_object.reason,
            }
            request_object.detailsOffBoarded = ""
        else:
            raise InvalidRequestException
        status_data = remove_none_values(status_data)
        user_data = {User.ID: request_object.userId, User.BOARDING_STATUS: status_data}
        user = User.from_dict(user_data)
        user_id = self._repo.update_user_profile(user)
        self._post_off_board(user_id, request_object.detailsOffBoarded)
        return Response(value=user_id)

    def _check_if_user_off_boarded_and_raise_error(self, user_id: str):
        user = self._repo.retrieve_simple_user_profile(user_id=user_id)
        if user.boardingStatus and user.boardingStatus.is_off_boarded():
            raise UserAlreadyOffboardedException

    def _check_if_reasons_off_boarded_is_valid(self):
        reasons = self.request_object.deployment.features.offBoardingReasons.reasons
        reasons_display_name = {reason.displayName for reason in reasons}
        if (
            not self.request_object.deployment.features.offBoardingReasons.otherReason
            and self.request_object.detailsOffBoarded not in reasons_display_name
        ):
            raise InvalidRequestException("Invalid details off boarded")

    def _post_off_board(self, user_id: str, detail: str):
        self._event_bus.emit(PostUserOffBoardEvent(user_id, detail))
