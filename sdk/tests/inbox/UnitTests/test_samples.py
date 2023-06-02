from sdk.common.utils.validators import remove_none_values
from sdk.inbox.models.confirm_message import (
    ConfirmMessageRequestObject,
    ConfirmMessageResponseObject,
)
from sdk.inbox.models.message import Message, SubmitterMessageReport, MessageStatusType
from sdk.inbox.models.search_message import (
    MessageSearchRequestObject,
    MessageSearchResponseObject,
)
from sdk.tests.inbox.UnitTests.common import MESSAGE_ID, USER_ID_1, USER_ID_2

SAMPLE_MESSAGE_TEXT = "text"


def sample_message(custom: bool = None):
    return remove_none_values(
        {
            Message.ID: MESSAGE_ID,
            Message.USER_ID: USER_ID_1,
            Message.SUBMITTER_ID: USER_ID_2,
            Message.SUBMITTER_NAME: "Test User",
            Message.TEXT: SAMPLE_MESSAGE_TEXT,
            Message.STATUS: MessageStatusType.READ.value,
            Message.CREATE_DATE_TIME: "2021-05-07T00:00:00Z",
            Message.UPDATE_DATE_TIME: "2021-05-07T00:00:00Z",
            Message.CUSTOM: custom,
        }
    )


def sample_submitter_message_report(custom: bool = None):
    return {
        SubmitterMessageReport.LATEST_MESSAGE: Message.from_dict(
            sample_message(custom)
        ),
        SubmitterMessageReport.UNREAD_MESSAGE_COUNT: 1,
    }


def sample_message_search_request_object():
    return {
        MessageSearchRequestObject.USER_ID: USER_ID_1,
        MessageSearchRequestObject.SUBMITTER_ID: USER_ID_2,
        MessageSearchRequestObject.SKIP: 1,
        MessageSearchRequestObject.LIMIT: 2,
    }


def sample_message_search_response():
    message = sample_message()
    return {MessageSearchResponseObject.MESSAGES: [message]}


def sample_message_confirmation_response():
    return {ConfirmMessageResponseObject.UPDATED: 1}


def sample_message_confirmation_request():
    return {ConfirmMessageRequestObject.MESSAGE_IDS: [MESSAGE_ID]}
