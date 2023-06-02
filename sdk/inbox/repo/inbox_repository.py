"""The Inbox Repository create and retrieve messages in/from database.

IMPORTANT, READ BEFORE CHANGING THIS FILE:
 This component is designed based on
 this link, and should not be changed due to regulatory guidelines:
 https://humatherapeutics.atlassian.net/wiki/spaces/~388818346/pages/3396927554/Free+text+messaging
 Other components which needs messaging functionality should access the
 database through this component.
"""
from abc import ABC, abstractmethod

from sdk.inbox.models.message import Message, SubmitterMessageReport


class InboxRepository(ABC):
    @abstractmethod
    def create_message(self, message: Message) -> str:
        """
        :param message: message object
        :return: id of the created message
        """
        raise NotImplementedError

    @abstractmethod
    def create_message_from_list(self, message_list: list[Message]):
        """
        :param message_list: list of message objects
        """
        raise NotImplementedError

    @abstractmethod
    def mark_messages_as_read(
        self, message_owner_id: str, message_ids: list[str]
    ) -> int:
        """
        :param message_owner_id: user id of the user who marks as read
        :param message_ids: list of message ids to be marked as read
        :return: number of the marked messages
        raise PermissionError if message_owner in the params is different than
        actual message_ids owner (even for one of the messages in the list)
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_submitters_first_messages(
        self, user_id: str
    ) -> list[SubmitterMessageReport]:
        """
        :param user_id: user id who is the receiver of the messages
        :return: list of submitter message reports
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_submitter_all_messages(
        self, user_id: str, submitter_id: str, skip: int, limit: int, custom: bool
    ) -> list[Message]:
        """
        :param user_id: user id who is the receiver of the messages
        :param submitter_id: submitter id to retrieve messages from
        :param skip: number of messages to skip
        :param limit: the limit of the messages to show
        :param custom: to show custom messages or predefined
        :return: list of submitter messages for this user
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_user_unread_messages_count(self, user_id: str) -> int:
        """
        :param user_id: user id to check number of unread messages
        :return: number of unread messages for this user
        """
        raise NotImplementedError
