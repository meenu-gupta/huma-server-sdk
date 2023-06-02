import logging
from datetime import datetime

from pymongo.client_session import ClientSession

from extensions.appointment.router.appointment_requests import (
    RetrieveAppointmentRequestObject,
)
from extensions.appointment.use_case.retrieve_appointment_use_case import (
    RetrieveAppointmentUseCase,
)
from extensions.authorization.services.authorization import AuthorizationService
from sdk.common.adapter.push_notification_adapter import (
    AndroidMessage,
    VoipApnsMessage,
    NotificationMessage,
)
from sdk.common.adapter.twilio.models import VideoTokenData
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification_for_voip_user,
)
from extensions.twilio_video.models.twilio_video import VideoCallLog, VideoCall
from extensions.twilio_video.repository.video_repository import VideoCallRepository
from sdk.common.adapter.twilio.twilio_video_adapter import TwilioVideoAdapter
from sdk.common.utils.inject import autoparams
from sdk.notification.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

MAX_WAIT_FOR_CALL_DURATION_SECONDS = 30


class TwilioVideoService:
    """Service to work  with Twilio video."""

    END_CALL_ACTION = "VIDEO_CALL_ENDED"
    CALL_ACTION = "OPEN_VIDEO_CALL"

    @autoparams()
    def __init__(self, adapter: TwilioVideoAdapter, repo: VideoCallRepository):
        self.adapter = adapter
        self.repo = repo

    def create_room(self, manager_id, user_id, appointment_id=None) -> tuple[str, str]:
        if appointment_id is not None:
            request_object = RetrieveAppointmentRequestObject.from_dict(
                {RetrieveAppointmentRequestObject.APPOINTMENT_ID: appointment_id}
            )
            RetrieveAppointmentUseCase().execute(request_object)

        video_call_id = self.repo.create_video_call(
            manager_id=manager_id, user_id=user_id, appointment_id=appointment_id
        )
        room_sid = self.adapter.create_room(video_call_id)
        return room_sid, video_call_id

    def generate_auth_token(self, identity, room_name):
        return self.adapter.generate_token(identity, room_name)

    def decode_token(self, token: str) -> VideoTokenData:
        return self.adapter.decode_token(token)

    def complete_video_call(self, room_sid):
        self.adapter.complete_room(room_sid=room_sid)

    def retrieve_rooms(self):
        return self.adapter.retrieve_rooms()

    def send_user_push_notification_invitation(self, user_id, room_name, manager_id):
        logger.info(f"Sending push notification to #userId{user_id}")
        identity = f"user:{user_id}"
        auth_token, ttl = self.adapter.generate_token(identity, room_name)
        manager_profile = AuthorizationService().retrieve_user_profile(manager_id)
        notification_data = {
            "roomName": room_name,
            "authToken": auth_token,
            "ttl": str(ttl),
            "click_action": self.CALL_ACTION,
            "managerName": f"{manager_profile.familyName} {manager_profile.givenName}",
        }
        notification_template = {"title": "Huma call", "body": "Huma video call"}
        prepare_and_send_push_notification_for_voip_user(
            user_id, self.CALL_ACTION, notification_template, notification_data
        )

    def send_user_push_notification_call_ended(self, user_id):
        logger.info(
            f"Sending push notification to #userId{user_id} about completed call"
        )
        android_msg = AndroidMessage(data={"click_action": self.END_CALL_ACTION})
        ios_msg = VoipApnsMessage(
            data={"operation": {"action": self.END_CALL_ACTION}},
            notification=NotificationMessage(
                title="Call Declined", body="Call was declined"
            ),
        )
        # for ios it needs to be sent as voip, for android as regular push
        NotificationService().push_for_voip_user(user_id=user_id, ios_voip=ios_msg)
        NotificationService().push_for_user(user_id=user_id, android=android_msg)

    def update_video_call(self, video_call):
        return self.repo.update_video_call(video_call)

    def retrieve_video_call(self, video_call_id):
        return self.repo.retrieve_video_call(video_call_id=video_call_id)

    def retrieve_call_participants(self, video_call_id):
        return self.adapter.retrieve_connected_participants_in_room(video_call_id)

    def finish_video_call_for_user(
        self, video_call_id: str, user_id: str, reason: str = None
    ):
        if reason is None:
            video_call = self.retrieve_video_call(video_call_id=video_call_id)

            for log in video_call.logs:
                if (
                    log.event == VideoCallLog.EventType.USER_JOINED.value
                    and log.identity == f"user:{user_id}"
                ):
                    reason = VideoCall.CallStatus.ANSWERED
                    break
            else:
                reason = self.find_reason_from_logs(video_call.logs)

        self.add_video_call_log(
            video_call_id,
            VideoCallLog.EventType.ROOM_FINISHED.value,
            f"user:{user_id}",
            reason=reason,
        )
        self.complete_video_call(video_call_id)

    @staticmethod
    def find_reason_from_logs(logs):
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        if logs:
            now = datetime.utcnow()
            wait_for_call_duration = max(
                (
                    now - datetime.strptime(log.createDateTime, date_format)
                ).total_seconds()
                for log in logs
            )
            if wait_for_call_duration > MAX_WAIT_FOR_CALL_DURATION_SECONDS:
                reason = VideoCall.CallStatus.MISSED
            else:
                reason = VideoCall.CallStatus.DECLINED
        else:
            reason = VideoCall.CallStatus.MISSED
        return reason

    def add_video_call_log(
        self, video_call_id: str, log_type: str, identity: str, reason: VideoCall.CallStatus = None
    ):
        log_obj = VideoCallLog.from_dict(
            {"event": log_type, "identity": identity}, ignored_fields=["type"]
        )
        return self.repo.add_video_call_log(
            video_call_id=video_call_id, video_call_log=log_obj, reason=reason
        )

    def check_video_call_log_exists(
        self, video_call_id: str, event: str, identity: str
    ):
        video_call = self.retrieve_video_call(video_call_id=video_call_id)
        for log in video_call.logs:
            if log.event == event and log.identity == identity:
                return True
        return False

    def delete_user_video(self, user_id: str, session: ClientSession = None):
        self.repo.delete_user_video(session=session, user_id=user_id)
