from enum import Enum


class InboxAction(Enum):
    SendMessageToUser = "SendMessageToUser"
    SendMessageToUserList = "SendMessageToUserList"
