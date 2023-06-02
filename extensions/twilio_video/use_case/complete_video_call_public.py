from extensions.authorization.services.authorization import AuthorizationService
from extensions.twilio_video.models.twilio_video import VideoCallLog
from extensions.twilio_video.repository.video_repository import VideoCallRepository
from extensions.twilio_video.router.twilio_video_request import (
    CompleteVideoCallRequestObject,
)
from sdk.common.adapter.twilio.twilio_video_adapter import TwilioVideoAdapter
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class CompleteVideoCallPublicUseCase(UseCase):
    request_object: CompleteVideoCallRequestObject

    @autoparams()
    def __init__(self, adapter: TwilioVideoAdapter, repo: VideoCallRepository):
        self._adapter = adapter
        self._repo = repo

    def process_request(self, request_object: CompleteVideoCallRequestObject):
        user_id = self._extract_user_id_from_request()
        self._check_user_exists(user_id)
        self._adapter.complete_room(request_object.callId)
        self.add_video_call_log(identity=f"user:{user_id}")

    def _extract_user_id_from_request(self):
        token_data = self._adapter.decode_token(self.request_object.token)
        return token_data.identity.split(":")[-1]

    def _check_user_exists(self, user_id: str):
        AuthorizationService().retrieve_simple_user_profile(user_id)

    def add_video_call_log(self, identity: str):
        log_data = {
            VideoCallLog.EVENT: VideoCallLog.EventType.ROOM_FINISHED.value,
            VideoCallLog.IDENTITY: identity,
        }
        log_obj = VideoCallLog.from_dict(log_data)
        return self._repo.add_video_call_log(self.request_object.callId, log_obj)
