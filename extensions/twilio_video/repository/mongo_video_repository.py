from datetime import datetime

from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from extensions.twilio_video.models.mongo_twilio_video import (
    MongoVideoCall,
    MongoVideoCallLog,
)
from extensions.twilio_video.models.twilio_video import VideoCall, VideoCallLog
from extensions.twilio_video.repository.video_repository import VideoCallRepository
from sdk.common.utils.validators import id_as_obj_id


class MongoVideoCallRepository(VideoCallRepository):
    VIDEO_CALL_COLLECTION = "video_call"

    @id_as_obj_id
    def create_video_call(
        self, manager_id: str, user_id: str, appointment_id: str = None
    ) -> str:
        video_call = MongoVideoCall(
            managerId=manager_id,
            userId=user_id,
            appointmentId=appointment_id,
            startDateTime=datetime.utcnow,
        ).save()
        return str(video_call.id)

    @id_as_obj_id
    def retrieve_video_call(self, video_call_id: str) -> VideoCall:
        video_call = MongoVideoCall.objects(id=video_call_id).first()
        if not video_call:
            raise ObjectDoesNotExist
        return VideoCall.from_dict(video_call.to_dict())

    @id_as_obj_id
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
        options = {VideoCall.USER_ID: user_id}
        if user_id != requester_id:
            options.update({VideoCall.MANAGER_ID: requester_id})

        if from_date_time:
            options.update({f"{VideoCall.START_DATE_TIME}__gte": from_date_time})

        if to_date_time:
            options.update({f"{VideoCall.START_DATE_TIME}__lte": to_date_time})

        if video_call_id:
            options.update({"id": video_call_id})

        results = MongoVideoCall.objects(**options).order_by("-startDateTime")
        if skip:
            results = results.skip(skip)
        if limit:
            results = results.limit(limit)

        return [VideoCall.from_dict(v.to_dict()) for v in results]

    def update_video_call(self, video_call: VideoCall) -> str:
        _dict = video_call.to_dict(include_none=False)
        mongo_video_call = MongoVideoCall.objects(id=video_call.id).first()
        if not mongo_video_call:
            raise ObjectDoesNotExist
        _dict.update({"updateDateTime": datetime.utcnow})
        if (
            mongo_video_call.roomStatus != video_call.roomStatus
        ) and video_call.roomStatus == "completed":
            _dict.update({"endDateTime": datetime.utcnow})
        _dict.pop(VideoCall.TYPE, None)
        mongo_video_call.update(**_dict)
        return str(mongo_video_call.id)

    @id_as_obj_id
    def delete_video_call(self, video_call_id: str):
        updated = MongoVideoCall.objects(id=video_call_id).delete()
        if not updated:
            raise ObjectDoesNotExist

    def add_video_call_log(
        self,
        video_call_id: str,
        video_call_log: VideoCallLog,
        reason: VideoCall.CallStatus = None,
    ):
        log_obj = MongoVideoCallLog(**video_call_log.to_dict(include_none=False))
        log_obj.createDateTime = datetime.utcnow()
        video_call: MongoVideoCall = MongoVideoCall.objects(id=video_call_id).first()
        video_call.logs.append(log_obj)
        if reason and not video_call.status:
            video_call.status = reason.value
        video_call.save()

    @id_as_obj_id
    def retrieve_video_call_logs(self, video_call_id: str, **query):
        query = {"id": video_call_id}
        video_calls = MongoVideoCall.objects(id=video_call_id, **query)
        video_calls = [
            VideoCall.from_dict(video_call.to_dict()) for video_call in video_calls
        ]
        return video_calls

    @id_as_obj_id
    def delete_user_video(self, session, user_id):
        db = MongoVideoCall._get_db()
        db[self.VIDEO_CALL_COLLECTION].delete_many(
            {MongoVideoCall.USER_ID: user_id}, session=session
        )
