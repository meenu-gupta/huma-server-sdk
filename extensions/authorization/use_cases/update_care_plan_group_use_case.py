import logging

import i18n

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.router.user_profile_request import (
    UpdateUserCarePlanGroupRequestObject,
)
from extensions.authorization.services.authorization import AuthorizationService
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams

logger = logging.getLogger(__file__)


class UpdateUserCarePlanGroupUseCase(UseCase):
    request_object: UpdateUserCarePlanGroupRequestObject = None

    @autoparams()
    def __init__(self, auth_repo: AuthorizationRepository):
        self._repo = auth_repo
        self.service = AuthorizationService()

    def execute(self, request_object):
        self.validate_care_plan_group_id(
            deployment_id=request_object.deploymentId,
            care_plan_group_id=request_object.carePlanGroupId,
        )
        self.request_object = request_object
        return super(UpdateUserCarePlanGroupUseCase, self).execute(request_object)

    def process_request(self, request_object):
        old_user = self.service.retrieve_user_profile(self.request_object.userId)
        if self.update_required(old_user):
            old_user.id = self.service.update_user_profile(request_object.to_user())
            self.create_care_plan_group_log(old_user.carePlanGroupId)
            self.send_care_plan_group_update_notifications(self.request_object.userId)

        return Response(value=old_user.id)

    def create_care_plan_group_log(self, previous_care_plan_group_id: str):
        log = self.request_object.to_care_plan_group_log()
        log.fromCarePlanGroupId = previous_care_plan_group_id
        self._repo.create_care_plan_group_log(log)

    def update_required(self, old_user: User):
        return old_user.carePlanGroupId != self.request_object.carePlanGroupId

    def send_care_plan_group_update_notifications(self, user_id: str):
        user = AuthorizedUser(self._repo.retrieve_user(user_id=user_id))
        locale = user.get_language()

        action = "CAREPLAN_GROUP_UPDATE"
        logger.debug(f"Sending care plan group update notification to #{user_id}")

        title = i18n.t("UpdateUserCarePlanGroup.title", locale=locale)
        body = i18n.t("UpdateUserCarePlanGroup.body", locale=locale)
        notification_template = {"title": title, "body": body}
        prepare_and_send_push_notification(
            user_id, action, notification_template, run_async=True
        )

    @staticmethod
    def validate_care_plan_group_id(deployment_id: str, care_plan_group_id):
        from extensions.deployment.service.deployment_service import DeploymentService

        deployment = DeploymentService().retrieve_deployment(deployment_id)
        deployment.validate_care_plan_group_id(care_plan_group_id)
