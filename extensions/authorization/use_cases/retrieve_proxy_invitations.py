from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.router.user_profile_request import (
    RetrieveProxyInvitationsRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveProxyInvitationsResponseObject,
)
from sdk.common.exceptions.exceptions import InvalidRequestException, ObjectDoesNotExist
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values


class RetrieveProxyInvitationsUseCase(UseCase):
    @autoparams()
    def __init__(
        self, invitation_repo: InvitationRepository, auth_repo: AuthorizationRepository
    ):
        self.invitation_repo = invitation_repo
        self.auth_repo = auth_repo

    def process_request(
        self, request_object: RetrieveProxyInvitationsRequestObject
    ) -> RetrieveProxyInvitationsResponseObject:
        proxy_status = RetrieveProxyInvitationsResponseObject.Response.ProxyStatus
        proxy_data = RetrieveProxyInvitationsResponseObject.Response.ProxyData
        proxy_ids = request_object.submitter.get_assigned_proxies()

        if proxy_ids:
            proxy_id = proxy_ids[0]
            user = self.auth_repo.retrieve_user(
                user_id=proxy_id[request_object.submitter.PROXY_ID]
            )

            data = proxy_data.from_dict(
                remove_none_values(
                    {
                        proxy_data.EMAIL: user.email,
                        proxy_data.GIVEN_NAME: user.givenName,
                        proxy_data.FAMILY_NAME: user.familyName,
                        proxy_data.PHONE_NUMBER: user.phoneNumber,
                    }
                )
            )

            status = (
                proxy_status.ACTIVE
                if user.finishedOnboarding
                else proxy_status.PENDING_ONBOARDING
            )
            return RetrieveProxyInvitationsResponseObject(status, data)

        try:
            invitation = self.invitation_repo.retrieve_proxy_invitation(
                user_id=request_object.submitter.id
            )
        except ObjectDoesNotExist:
            msg = "Patient has no proxy invitations"
            raise InvalidRequestException(msg)

        pending_signup = proxy_status.PENDING_SIGNUP.value
        data = proxy_data.from_dict({proxy_data.EMAIL: invitation.email})
        return RetrieveProxyInvitationsResponseObject(
            pending_signup, invitation_id=invitation.id, proxy=data
        )
