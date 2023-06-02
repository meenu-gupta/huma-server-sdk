from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.invitation_request_objects import (
    InvitationValidityRequestObject,
)
from extensions.authorization.router.invitation_response_objects import (
    InvitationValidityResponseObject,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import validate_shortened_invitation_code
from sdk.phoenix.config.server_config import PhoenixServerConfig


class InvitationValidityUseCase(UseCase):
    @autoparams()
    def __init__(
        self, invitation_repo: InvitationRepository, config: PhoenixServerConfig
    ):
        self._invitation_repo = invitation_repo
        self._config = config

    def process_request(self, request_object: InvitationValidityRequestObject):
        # we need just to try to get an invitation.
        # if found we return an empty resp. otherwise, 404 is raised
        invitation_code = request_object.invitationCode
        if (
            validate_shortened_invitation_code(invitation_code)
            and len(invitation_code)
            == self._config.server.invitation.shortenedCodeLength
        ):
            invitation = self._invitation_repo.retrieve_invitation(
                shortened_code=invitation_code
            )
        else:
            invitation = self._invitation_repo.retrieve_invitation(code=invitation_code)
        return InvitationValidityResponseObject(code=invitation.code, valid=True)
