import logging
from dataclasses import dataclass
from enum import Enum

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.common.adapter.push_notification_adapter import (
    AndroidMessage,
    ApnsMessage,
    NotificationMessage,
)
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from extensions.authorization.services.authorization import AuthorizationService
from sdk import meta
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.utils.inject import autoparams
from sdk.common.utils.json_utils import replace_values
from sdk.common.utils.validators import (
    validate_id,
    must_be_only_one_of,
    remove_none_values,
    datetime_now,
)
from sdk.common.utils.convertible import required_field, default_field
from sdk.notification.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@dataclass
class KeyAction(CalendarEvent):
    MODULE_ACTION = "KEYACTION_OPEN_MODULE"
    LEARN_ACTION = "KEYACTION_OPEN_LEARN"
    OPEN_APP_ACTION = "KEYACTION_OPEN_APP"
    CAREPLAN_GROUP_UPDATE = "CAREPLAN_GROUP_UPDATE"

    LEARN_ARTICLE_ID = "learnArticleId"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"
    KEY_ACTION_CONFIG_ID = "keyActionConfigId"
    DEPLOYMENT_ID = "deploymentId"
    EXTRA_FIELD_NAMES = (
        LEARN_ARTICLE_ID,
        MODULE_ID,
        MODULE_CONFIG_ID,
        KEY_ACTION_CONFIG_ID,
        DEPLOYMENT_ID,
    )

    keyActionConfigId: str = required_field(metadata=meta(validate_id))
    learnArticleId: str = default_field(metadata=meta(validate_id))
    moduleId: str = default_field()
    moduleConfigId: str = default_field()
    deploymentId: str = default_field(metadata=meta(validate_id, value_to_field=str))

    def __str__(self):
        return f"Key action [{self.moduleId}]"

    @classmethod
    def validate(cls, event):
        must_be_only_one_of(
            learnArticleId=event.learnArticleId,
            moduleId=event.moduleId and event.moduleConfigId,
        )

    def execute(self, run_async=True):
        action = self._get_action("apns")

        if action == self.OPEN_APP_ACTION:
            details = self.OPEN_APP_ACTION
        elif action == self.MODULE_ACTION:
            details = self.moduleId
        else:
            details = self.learnArticleId

        logger.debug(
            f"Sending key action {action} notification for #{self.userId}/#{details}"
        )

        user = AuthorizationService().retrieve_user_profile(user_id=self.userId)
        user = AuthorizedUser(user)
        notification_template = replace_values(
            {"title": self.title, "body": self.description},
            user.localization,
        )
        notification_data = remove_none_values(
            {
                "action": action,
                "moduleId": self.moduleId,
                "moduleConfigId": self.moduleConfigId,
                "learnArticleId": self.learnArticleId,
                "keyActionId": self.parentId,
                "sentDateTime": datetime_now(),
            }
        )
        android_action = self._get_action("fcm")
        android_message = AndroidMessage(
            data={
                "click_action": android_action,
                **notification_template,
                **{**notification_data, "action": android_action},
            }
        )
        ios_message = ApnsMessage(
            notification=NotificationMessage(**notification_template),
            data={"operation": notification_data},
        )
        NotificationService().push_for_user(
            self.userId, android=android_message, ios=ios_message, run_async=run_async
        )
        send_notification_to_proxy(
            user_id=self.userId,
            deployment_id=self.deploymentId,
            notification_template=notification_template,
            notification_data=notification_data,
            action=action,
            run_async=run_async,
        )

    def _get_action(self, msg_type: str):
        from extensions.module_result.modules import (
            AdditionalQoLModule,
            AZGroupKeyActionTriggerModule,
            AZFurtherPregnancyKeyActionTriggerModule,
            AZScreeningQuestionnaireModule,
            BackgroundInformationModule,
            BreastFeedingUpdateModule,
            BreastFeedingStatusModule,
            FeverAndPainDrugsModule,
            HealthStatusModule,
            InfantFollowUpModule,
            MedicalHistoryModule,
            OtherVaccineModule,
            PostVaccinationModule,
            PregnancyFollowUpModule,
            PregnancyStatusModule,
            PregnancyUpdateModule,
            PROMISGlobalHealthModule,
            VaccinationDetailsModule,
        )

        no_action_modules = (
            AdditionalQoLModule.moduleId,
            AZGroupKeyActionTriggerModule.moduleId,
            AZFurtherPregnancyKeyActionTriggerModule.moduleId,
            AZScreeningQuestionnaireModule.moduleId,
            BackgroundInformationModule.moduleId,
            BreastFeedingStatusModule.moduleId,
            BreastFeedingUpdateModule.moduleId,
            FeverAndPainDrugsModule.moduleId,
            HealthStatusModule.moduleId,
            InfantFollowUpModule.moduleId,
            MedicalHistoryModule.moduleId,
            OtherVaccineModule.moduleId,
            PostVaccinationModule.moduleId,
            PregnancyFollowUpModule.moduleId,
            PregnancyStatusModule.moduleId,
            PregnancyUpdateModule.moduleId,
            PROMISGlobalHealthModule.moduleId,
            VaccinationDetailsModule.moduleId,
        )
        if self.moduleId in no_action_modules:
            if msg_type == "apns":
                return self.OPEN_APP_ACTION
            return self.CAREPLAN_GROUP_UPDATE

        return self.MODULE_ACTION if self.moduleId else self.LEARN_ACTION

    def pack_extra_fields(self):
        extra_fields = {}
        for field_name in self.EXTRA_FIELD_NAMES:
            extra_fields[field_name] = getattr(self, field_name, None)
            setattr(self, field_name, None)
        self.extraFields = remove_none_values(extra_fields)


@autoparams("auth_repo")
def send_notification_to_proxy(
    user_id: str,
    deployment_id: str,
    notification_template: dict,
    notification_data: dict,
    action: str,
    run_async: bool,
    auth_repo: AuthorizationRepository,
):
    if not deployment_id:
        return

    participant = auth_repo.retrieve_user(user_id=user_id)
    authz_user = AuthorizedUser(participant, deployment_id)
    proxies = authz_user.get_assigned_proxies()
    if not proxies:
        return
    for proxy in proxies:
        prepare_and_send_push_notification(
            user_id=proxy[AuthorizedUser.PROXY_ID],
            action=action,
            notification_template=notification_template,
            notification_data=notification_data,
            run_async=run_async,
        )


class Action(Enum):
    CreateKeyActionLog = "CreateKeyActionLog"
