from typing import Optional

from extensions.twilio_video.repository.video_repository import VideoCallRepository
from extensions.twilio_video.router.response import RetrieveCallsResponseObject
from extensions.twilio_video.router.twilio_video_request import (
    RetrieveCallsRequestObject,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class RetrieveVideoCallsUseCase(UseCase):
    request_object: Optional[RetrieveCallsRequestObject] = None

    @autoparams()
    def __init__(self, repo: VideoCallRepository):
        self.repo = repo

    def process_request(self, request_object: RetrieveCallsRequestObject):
        video_calls = self.repo.retrieve_video_calls(
            user_id=request_object.userId,
            requester_id=request_object.requesterId,
            skip=request_object.skip,
            limit=request_object.limit,
            video_call_id=request_object.video_call_id,
        )
        for call in video_calls:
            call.logs = []

        return RetrieveCallsResponseObject(video_calls)
