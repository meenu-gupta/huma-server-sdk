import logging

from extensions.twilio_video.repository.mongo_video_repository import (
    MongoVideoCallRepository,
)
from extensions.twilio_video.repository.video_repository import VideoCallRepository

logger = logging.getLogger(__name__)


def bind_twilio_video_repository(binder, config):
    binder.bind_to_provider(VideoCallRepository, lambda: MongoVideoCallRepository())
    logger.debug(f"VideoCallRepository bind toMongoVideoCallRepository")
