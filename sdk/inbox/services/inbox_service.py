import logging
from datetime import datetime

from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.localization.utils import Language
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from i18n import t
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.inbox.events.auth_events import PreCreateMessageEvent
from sdk.inbox.models.message import Message, MessageStatusType
from sdk.inbox.models.search_message import MessageSearchResponseObject
from sdk.inbox.repo.inbox_repository import InboxRepository

logger = logging.getLogger(__name__)


class InboxService:
    INBOX_ACTION = "OPEN_MESSAGING"

    @autoparams()
    def __init__(self, repo: InboxRepository, event_bus: EventBusAdapter):
        self._repo = repo
        self._event_bus = event_bus

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

    def send_message(self, message: Message, locale: str = Language.EN) -> str:
        self._pre_send_event(message)
        message.createDateTime = message.updateDateTime = datetime.utcnow()
        message.status = MessageStatusType.DELIVERED
        result = self._repo.create_message(message)
        unread_count = self._repo.retrieve_user_unread_messages_count(message.userId)
        self._send_push_notification(
            message.userId,
            message.submitterId,
            locale,
            message.custom,
            unread=unread_count,
        )
        return result

    def _pre_send_event(self, message: Message):
        event = PreCreateMessageEvent(
            text=message.text,
            custom=message.custom,
            submitter_id=message.submitterId,
            receiver_id=message.userId,
        )
        self._event_bus.emit(event, raise_error=True)

    def retrieve_messages(
        self, user_id: str, submitter_id: str, skip: int, limit: int, custom: bool
    ):
        messages = self._repo.retrieve_submitter_all_messages(
            user_id=user_id,
            submitter_id=submitter_id,
            skip=skip,
            limit=limit,
            custom=custom,
        )
        return MessageSearchResponseObject(messages)

    def retrieve_submitters_first_messages(self, user_id: str) -> dict[str, list[dict]]:
        summary = self._repo.retrieve_submitters_first_messages(user_id)
        unread_message_count = sum([s.unreadMessageCount for s in summary])
        submitters_summary = [s.to_dict() for s in summary]
        return {"messages": submitters_summary, "unreadMessages": unread_message_count}

    def confirm_messages(self, message_owner_id: str, message_ids: list[str]):
        return self._repo.mark_messages_as_read(message_owner_id, message_ids)
