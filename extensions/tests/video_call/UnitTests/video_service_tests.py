import unittest
from unittest.mock import patch, MagicMock

from freezegun import freeze_time

from extensions.twilio_video.models.twilio_video import VideoCall, VideoCallLog
from extensions.twilio_video.service.video_service import TwilioVideoService

SERVICE_PATH = "extensions.twilio_video.service.video_service"


class MockRepo(MagicMock):
    retrieve_video_call = MagicMock(return_value=VideoCall(logs=[]))


def sample_logs():
    logs = [
        {"event": "room-created", "createDateTime": "2022-06-22T13:32:37.447000Z"},
        {
            "event": "participant-connected",
            "identity": "manager:5f439fde5858ea448033b84d",
            "createDateTime": "2022-06-22T13:32:37.447000Z",
        },
        {
            "event": "participant-connected",
            "identity": "user:5f43a2765858ea448033b84e",
            "createDateTime": "2022-06-22T13:32:37.447000Z",
        },
        {
            "event": "participant-disconnected",
            "identity": "manager:5f439fde5858ea448033b84d",
            "createDateTime": "2022-06-22T13:32:37.447000Z",
        },
        {"event": "room-ended", "createDateTime": "2022-06-22T13:32:37.447000Z"},
    ]
    return [VideoCallLog.from_dict(d) for d in logs]


class VideoServiceTestCase(unittest.TestCase):
    USER_ID = ""
    MANAGER_ID = ""
    CALL_ID = ""

    def setUp(self):
        self.service = TwilioVideoService(
            MagicMock(),
            MockRepo(),
        )

    def test_create_room(self):
        self.service.create_room(self.MANAGER_ID, self.USER_ID)
        self.service.repo.create_video_call.assert_called_once_with(
            manager_id=self.MANAGER_ID, user_id=self.USER_ID, appointment_id=None
        )
        self.service.adapter.create_room.assert_called_once()

    @patch(f"{SERVICE_PATH}.VideoCallLog")
    def test_finish_video_call_for_user(self, video_call_log):
        self.service.finish_video_call_for_user(self.CALL_ID, self.USER_ID)
        video_call_log.from_dict.assert_called_once_with(
            {
                "event": video_call_log.EventType.ROOM_FINISHED.value,
                "identity": f"user:{self.USER_ID}",
            },
            ignored_fields=["type"],
        )

    @patch(f"{SERVICE_PATH}.VideoCallLog")
    def test_finish_video_call_for_user_with_reason(self, video_call_log):
        self.service.finish_video_call_for_user(
            self.CALL_ID, self.USER_ID, VideoCall.CallStatus.DECLINED
        )
        video_call_log.from_dict.assert_called_once_with(
            {
                "event": video_call_log.EventType.ROOM_FINISHED.value,
                "identity": f"user:{self.USER_ID}",
            },
            ignored_fields=["type"],
        )

    @freeze_time("2021-01-01T10:00:00.000Z")
    def test_find_reason_from_logs(self):
        reason = self.service.find_reason_from_logs(sample_logs())
        self.assertEqual(VideoCall.CallStatus.DECLINED, reason)
