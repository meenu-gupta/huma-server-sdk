import logging
from typing import Any

from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.router.user_profile_request import (
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.router.deployment_requests import (
    WithdrawEConsentRequestObject,
)
from extensions.exceptions import EconsentWithdrawalError
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__file__)


class WithdrawEConsentUseCase(UseCase):
    @autoparams()
    def __init__(self, ec_repo: EConsentRepository):
        self._econsent_repo = ec_repo

    def process_request(self, request_object: WithdrawEConsentRequestObject):
        self._check_latest_econsent(request_object)
        self._withdraw_econsent(request_object)
        return self._off_board_user(request_object)

    def _withdraw_econsent(
        self, request_object: WithdrawEConsentRequestObject
    ) -> dict[str, Any]:
        return self._econsent_repo.withdraw_econsent(
            log_id=request_object.logId,
        )

    def _check_latest_econsent(self, request_object: WithdrawEConsentRequestObject):
        econsent = self._econsent_repo.retrieve_latest_econsent(
            deployment_id=request_object.deploymentId
        )
        if econsent.id != request_object.econsentId:
            raise ObjectDoesNotExist
        econsent_log = self._econsent_repo.retrieve_signed_econsent_log(
            log_id=request_object.logId, user_id=request_object.userId
        )
        if econsent_log[EConsentLog.REVISION] != econsent.revision:
            raise EconsentWithdrawalError

    def _off_board_user(
        self, request_object: WithdrawEConsentRequestObject
    ) -> Response:
        request_obj = SystemOffBoardUserRequestObject.from_dict(
            {
                SystemOffBoardUserRequestObject.USER_ID: request_object.userId,
                SystemOffBoardUserRequestObject.REASON: BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF,
            }
        )
        return OffBoardUserUseCase().execute(request_obj)
