import logging

from extensions.twilio_video.service.video_service import TwilioVideoService
from sdk.auth.events.delete_user_event import DeleteUserEvent
from extensions.common.monitoring import report_exception

logger = logging.getLogger(__name__)


def on_user_delete_callback(event: DeleteUserEvent):
    service = TwilioVideoService()
    try:
        service.delete_user_video(session=event.session, user_id=event.user_id)
    except Exception as error:
        logger.error(f"Error on deleting user video: {str(error)}")
        report_exception(
            error,
            context_name="DeleteUserVideo",
            context_content={"userId": event.user_id},
        )
        raise error
