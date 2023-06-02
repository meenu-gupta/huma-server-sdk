import logging

from twilio.base.exceptions import TwilioRestException
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
from twilio.rest.video.v1.room import RoomInstance
from twilio.rest.video.v1.room.room_participant import ParticipantInstance

from sdk.common.adapter.twilio.exceptions import (
    RoomAlreadyClosedException,
    TokenNotValidException,
)
from sdk.common.adapter.twilio.models import VideoTokenData
from sdk.common.adapter.twilio.twilio_video_config import TwilioVideoAdapterConfig
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class TwilioVideoAdapter:
    def __init__(self, config: PhoenixServerConfig):
        self.config: TwilioVideoAdapterConfig = config.server.adapters.twilioVideo
        self.domain = config.server.hostUrl
        self.twilio_client = Client(self.config.accountSid, self.config.authToken)

    def create_room(self, room_name):
        # TODO change to config variable
        callback_url = f"https://{self.domain}/api/extensions/v1beta/video/callbacks"
        room = self.twilio_client.video.rooms.create(
            record_participants_on_connect=False,
            status_callback=callback_url,
            type=RoomInstance.RoomType.GO,
            unique_name=room_name,
            media_region=self.config.mediaRegion,
        )

        return str(room.sid)

    def complete_room(self, room_sid):
        try:
            self.twilio_client.video.rooms(room_sid).update(
                status=RoomInstance.RoomStatus.COMPLETED
            )
        except TwilioRestException:
            raise RoomAlreadyClosedException

    def generate_token(self, identity: str, room_name: str):

        token = AccessToken(
            self.config.accountSid,
            self.config.apiKey,
            self.config.apiSecret,
            identity=identity,
        )

        # Create a Video grant and add to token
        video_grant = VideoGrant(room=room_name)
        token.add_grant(video_grant)
        return token.to_jwt().decode("utf-8"), token.ttl

    def decode_token(self, token: str) -> VideoTokenData:
        try:
            token_obj = AccessToken.from_jwt(token.encode("utf-8"))
            return VideoTokenData.from_dict(token_obj.payload["grants"])
        except Exception as e:
            raise TokenNotValidException(f"Token is not valid: {e}")

    def retrieve_rooms(self):
        return self.twilio_client.video.rooms.list()

    def retrieve_connected_participants_in_room(self, room_name):
        return self.twilio_client.video.rooms(room_name).participants.list(
            status=ParticipantInstance.Status.CONNECTED
        )
