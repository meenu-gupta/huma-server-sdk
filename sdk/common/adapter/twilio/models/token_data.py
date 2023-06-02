from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field


@convertibleclass
class VideoData:
    room: str = required_field()


@convertibleclass
class VideoTokenData:
    identity: str = required_field()
    video: VideoData = default_field()
