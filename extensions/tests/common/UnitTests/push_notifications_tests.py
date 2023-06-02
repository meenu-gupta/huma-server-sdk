import datetime
import unittest
from unittest.mock import patch

from freezegun import freeze_time

from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
    prepare_and_send_push_notification_for_voip_user,
)
from sdk.common.adapter.push_notification_adapter import (
    AndroidMessage,
    NotificationMessage,
    ApnsMessage,
    VoipApnsMessage,
)


NOTIFICATION_SERVICE_PATH = (
    "sdk.common.push_notifications.push_notifications_utils.NotificationService"
)


class PushNotificationTestCase(unittest.TestCase):
    @patch(NOTIFICATION_SERVICE_PATH)
    def test_prepare_and_send_push_notification(self, mocked_notification_service):
        action = "test_action"
        user_id = "dummy_id"
        title = "Title"
        body = "Body"
        notification_template = {"title": title, "body": body}
        str_dt = "2020-12-01T00:00:00.000Z"

        with freeze_time(datetime.datetime(2020, 12, 1)):
            prepare_and_send_push_notification(
                user_id=user_id,
                action=action,
                notification_template=notification_template,
            )
            mocked_notification_service().push_for_user.assert_called_with(
                user_id,
                android=AndroidMessage(
                    notification=None,
                    data={
                        "click_action": action,
                        "title": title,
                        "body": body,
                        "action": action,
                        "sentDateTime": str_dt,
                    },
                ),
                ios=ApnsMessage(
                    notification=NotificationMessage(title=title, body=body),
                    data={"operation": {"action": action, "sentDateTime": str_dt}},
                ),
                run_async=False,
            )

    @patch(NOTIFICATION_SERVICE_PATH)
    def test_prepare_and_send_push_notification_for_voip_user(
        self, mocked_notification_service
    ):
        action = "test_action"
        user_id = "dummy_id"
        title = "Title"
        body = "Body"
        notification_template = {"title": title, "body": body}
        str_dt = "2020-12-01T00:00:00.000Z"

        with freeze_time(datetime.datetime(2020, 12, 1)):
            prepare_and_send_push_notification_for_voip_user(
                user_id=user_id,
                action=action,
                notification_template=notification_template,
            )
            mocked_notification_service().push_for_voip_user.assert_called_with(
                user_id,
                android=AndroidMessage(
                    notification=None,
                    data={
                        "click_action": action,
                        "title": title,
                        "body": body,
                        "action": action,
                        "sentDateTime": str_dt,
                    },
                ),
                ios_voip=VoipApnsMessage(
                    notification=NotificationMessage(title=title, body=body),
                    data={"action": action, "sentDateTime": str_dt},
                ),
            )


if __name__ == "__main__":
    unittest.main()
