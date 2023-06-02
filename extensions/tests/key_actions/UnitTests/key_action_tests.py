import unittest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from extensions.key_action.models.key_action_log import KeyAction
from extensions.key_action.use_case.key_action_requests import (
    CreateKeyActionLogRequestObject,
)
from sdk.calendar.utils import get_dt_from_str

VALID_OBJECT_ID = "60019625090d076320280736"

MODEL_PATH = "extensions.key_action.models.key_action_log"


class MockAuthzUser(MagicMock):
    @property
    def localization(self):
        return {"hu_ka_title": "Success", "hu_ka_description": "Successful"}


class KeyActionTestCase(unittest.TestCase):
    def test_success_key_action_to_dict(self):
        key_action = KeyAction(
            keyActionConfigId=VALID_OBJECT_ID,
            learnArticleId=VALID_OBJECT_ID,
            moduleConfigId=VALID_OBJECT_ID,
            moduleId=VALID_OBJECT_ID,
        )
        res = key_action.to_dict()
        self.assertEqual(res["extraFields"]["keyActionConfigId"], VALID_OBJECT_ID)
        self.assertEqual(res["extraFields"]["learnArticleId"], VALID_OBJECT_ID)
        self.assertEqual(res["extraFields"]["moduleConfigId"], VALID_OBJECT_ID)
        self.assertEqual(res["extraFields"]["moduleId"], VALID_OBJECT_ID)

    @patch(f"{MODEL_PATH}.AuthorizationService", MagicMock())
    @patch(f"{MODEL_PATH}.AuthorizedUser", MockAuthzUser)
    @patch(f"{MODEL_PATH}.send_notification_to_proxy", MagicMock())
    @patch(f"{MODEL_PATH}.NotificationService")
    def test_success_translated(self, mock_notif):
        title = "hu_ka_title"
        description = "hu_ka_description"
        key_action = KeyAction(
            title=title,
            description=description,
            userId="testUserId",
        )

        key_action.execute()
        kwargs = mock_notif().push_for_user.call_args.kwargs

        localization = MockAuthzUser().localization
        self.assertEqual(localization.get(title), kwargs["android"].data["title"])
        self.assertEqual(localization.get(description), kwargs["android"].data["body"])
        self.assertEqual(localization.get(title), kwargs["ios"].notification.title)
        self.assertEqual(localization.get(description), kwargs["ios"].notification.body)

    @patch(f"{MODEL_PATH}.AuthorizationService", MagicMock())
    @patch(f"{MODEL_PATH}.AuthorizedUser", MockAuthzUser)
    @patch(f"{MODEL_PATH}.send_notification_to_proxy", MagicMock())
    @patch(f"{MODEL_PATH}.NotificationService")
    def test_execute_proper_payload(self, mock_notif):
        parent_id = "testParentId"
        key_action = KeyAction(
            id="testKaId",
            title="Test",
            description="Here",
            userId="testUserId",
            parentId=parent_id,
        )

        key_action.execute()
        kwargs = mock_notif().push_for_user.call_args.kwargs

        self.assertEqual(parent_id, kwargs["android"].data["keyActionId"])
        self.assertEqual(parent_id, kwargs["ios"].data["operation"]["keyActionId"])


class CreateKeyActionLogTestCase(unittest.TestCase):
    def test_create_calendar_log_request_obj_as_timezone(self):
        test_cases = (
            ("UTC", timedelta(hours=0)),
            ("Europe/Kiev", timedelta(hours=2)),
            ("Asia/Kolkata", timedelta(hours=5, minutes=30)),
        )
        start = get_dt_from_str("2021-01-01T10:00:00.000Z")
        end = get_dt_from_str("2021-01-08T10:00:00.000Z")

        for timezone, delta in test_cases:
            log = CreateKeyActionLogRequestObject(startDateTime=start, endDateTime=end)
            log.as_timezone(timezone)

            self.assertEqual(delta, log.startDateTime - start)
            self.assertEqual(delta, log.endDateTime - end)
