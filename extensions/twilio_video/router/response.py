from extensions.twilio_video.models.twilio_video import VideoCall
from sdk import convertibleclass
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import required_field


class RetrieveCallsResponseObject(response_object.Response):
    @convertibleclass
    class Response:
        CALLS = "calls"

        calls: list[VideoCall] = required_field()

    def __init__(self, calls: list[VideoCall]):
        value = self.Response.from_dict({self.Response.CALLS: calls})
        super().__init__(value)
