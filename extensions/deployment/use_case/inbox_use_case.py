from flask import g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.inbox.use_case.inbox_use_case import SendMessageToUserListUseCase


class SendMessageToDeploymentPatientListUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: DeploymentRepository, auth_repo: AuthorizationRepository):
        self._repo = repo
        self._auth_repo = auth_repo

    def process_request(self, request_object):
        submitter_deployment_id = g.authz_user.deployment_id()
        if request_object.allUsers:
            request_object.userIds = self._auth_repo.retrieve_user_ids_in_deployment(
                submitter_deployment_id
            )
        else:
            self._validate_submitter_and_users_be_in_one_deployment(
                submitter_deployment_id, request_object.userIds
            )

        response_object = SendMessageToUserListUseCase().execute(request_object)
        return response_object

    def _validate_submitter_and_users_be_in_one_deployment(
        self, submitter_deployment_id, user_ids
    ):
        users = self._auth_repo.retrieve_users_by_id_list(user_id_list=user_ids)
        if not all(
            [
                submitter_deployment_id in AuthorizedUser(user).deployment_ids()
                for user in users
            ]
        ):
            raise PermissionDenied("Access of different resources")
