"""The Inbox Use Case prepares messages for storing in the database.
 In addition, it sends push notifications to users informing them of
 new messages.

 IMPORTANT, READ BEFORE CHANGING THIS FILE:
 The use case and corresponding repository are designed based on
 this link, and should not be changed due to regulatory guidelines:
 https://humatherapeutics.atlassian.net/wiki/spaces/~388818346/pages/3396927554/Free+text+messaging
 This use case may be used by other use cases or routers out of this component.
"""
from flask import g
from i18n import t

from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.localization.utils import Language
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.events.auth_events import (
    PreCreateMessageEvent,
)
from sdk.inbox.models.message import Message
from sdk.inbox.repo.inbox_repository import InboxRepository
from sdk.inbox.router.inbox_request import SendMessageToUserListRequestObject


class SendMessageToUserListUseCase(UseCase):
    INBOX_ACTION = "OPEN_MESSAGING"

    @autoparams()
    def __init__(
        self,
        repo: InboxRepository,
        event_bus: EventBusAdapter,
        auth_repo: AuthorizationRepository,
    ):
        self._repo = repo
        self._event_bus = event_bus
        self._auth_repo = auth_repo

    def _send_push_notification(
        self,
        user_id: str,
        submitter_id: str,
        locale: str,
        custom: bool,
        unread: int = None,
        run_async: bool = False,
    ):
        notification_template = {
            "title": t("Notification.inbox.user.title", locale=locale),
            "body": t("Notification.inbox.user.body", locale=locale),
        }
        notification_data = {
            "action": self.INBOX_ACTION,
            "submitterId": submitter_id,
            "isCustom": custom,
        }
        prepare_and_send_push_notification(
            user_id=user_id,
            action=self.INBOX_ACTION,
            notification_template=notification_template,
            notification_data=remove_none_values(notification_data),
            unread=unread,
            run_async=run_async,
        )

    def process_request(
        self, request_object: SendMessageToUserListRequestObject
    ) -> Response:
        message_list = []
        users_list = self._auth_repo.retrieve_users_by_id_list(
            user_id_list=request_object.userIds
        )
        for user in users_list:
            message = Message.from_dict(
                {
                    Message.SUBMITTER_ID: request_object.submitterId,
                    Message.USER_ID: user.id,
                    Message.SUBMITTER_NAME: request_object.submitterName,
                    Message.TEXT: request_object.text,
                    Message.CUSTOM: request_object.custom,
                }
            )
            self._pre_send_event(message)
            message.locale = user.language or Language.EN
            message_list.append(message)

        self._repo.create_message_from_list(message_list)
        for message in message_list:
            unread_count = self._repo.retrieve_user_unread_messages_count(
                message.userId
            )
            self._send_push_notification(
                message.userId,
                message.submitterId,
                message.locale,
                message.custom,
                unread=unread_count,
            )
        return Response({"SentMessages": len(request_object.userIds)})

    def _pre_send_event(self, message: Message):
        event = PreCreateMessageEvent(
            text=message.text,
            custom=message.custom,
            submitter_id=message.submitterId,
            receiver_id=message.userId,
        )
        self._event_bus.emit(event, raise_error=True)
