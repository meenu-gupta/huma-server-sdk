from abc import ABC, abstractmethod
from datetime import datetime

from extensions.twilio_video.models.twilio_video import VideoCall, VideoCallLog


class VideoCallRepository(ABC):
    @abstractmethod
    def create_video_call(
        self, manager_id: str, user_id: str, appointment_id: str = None
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_video_call(self, video_call_id: str) -> VideoCall:
        raise NotImplementedError

    @abstractmethod
    def retrieve_video_calls(
        self,
        user_id: str,
        requester_id: str,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
        skip: int = None,
        limit: int = None,
        video_call_id: str = None,
    ) -> list[VideoCall]:
        raise NotImplementedError

    @abstractmethod
    def update_video_call(self, video_call: VideoCall) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_video_call(self, video_call_id: str):
        raise NotImplementedError

    @abstractmethod
    def add_video_call_log(
        self,
        video_call_id: str,
        video_call_log: VideoCallLog,
        reason: VideoCall.CallStatus = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def delete_user_video(self, session, user_id):
        raise NotImplementedError
