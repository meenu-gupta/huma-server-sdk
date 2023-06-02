from sdk.common.adapter.push_notification_adapter import (
    AndroidMessage,
    ApnsMessage,
    NotificationMessage,
    VoipApnsMessage,
)
from sdk.common.utils.validators import datetime_now
from sdk.notification.services.notification_service import NotificationService


def prepare_and_send_push_notification(
    user_id: str,
    action: str,
    notification_template: dict,
    notification_data: dict = None,
    unread: int = None,
    run_async: bool = False,
):
    notification_data = _set_notification_data(action, notification_data)

    android_message_data = {
        "click_action": action,
        **notification_template,
        **notification_data,
    }
    android_message = AndroidMessage(data=android_message_data)
    ios_message_data = {
        "notification": NotificationMessage(**notification_template),
        "data": {"operation": notification_data},
    }
    if unread is not None:
        ios_message_data.update({"badge": unread})
    ios_message = ApnsMessage(**ios_message_data)
    NotificationService().push_for_user(
        user_id, android=android_message, ios=ios_message, run_async=run_async
    )


def prepare_and_send_push_notification_for_voip_user(
    user_id: str,
    action: str,
    notification_template: dict,
    notification_data: dict = None,
):
    notification_data = _set_notification_data(action, notification_data)

    android_message_data = {
        "click_action": action,
        **notification_template,
        **notification_data,
    }
    android_message = AndroidMessage(data=android_message_data)
    ios_message = VoipApnsMessage(
        notification=NotificationMessage(**notification_template),
        data=notification_data,
    )
    NotificationService().push_for_voip_user(
        user_id, android=android_message, ios_voip=ios_message
    )


def _set_notification_data(action: str, notification_data: dict) -> dict:
    notification_data = notification_data or {}
    for key, val in notification_data.items():
        if type(val) is bool:
            notification_data[key] = str(val).lower()
    return {**notification_data, "action": action, "sentDateTime": datetime_now()}
