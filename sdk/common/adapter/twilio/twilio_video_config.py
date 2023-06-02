from dataclasses import field
from enum import Enum

from twilio.rest.insights.v1.room import RoomInstance

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field
from sdk.common.utils.validators import validate_twilio_media_region


@convertibleclass
class MediaRegion(RoomInstance.TwilioRealm, Enum):
    @staticmethod
    def get_valid_regions():
        regions = []
        for attr in RoomInstance.TwilioRealm.__dict__:
            value = getattr(MediaRegion, attr)
            if not callable(value) and not attr.startswith("__"):
                regions.append(value)
        return regions


@convertibleclass
class TwilioVideoAdapterConfig:
    ACCOUNT_SID = "accountSid"
    AUTH_TOKEN = "authToken"
    API_KEY = "apiKey"
    API_SECRET = "apiSecret"
    MEDIA_REGION = "mediaRegion"

    accountSid: str = required_field()
    authToken: str = required_field()
    apiKey: str = required_field()
    apiSecret: str = required_field()
    mediaRegion: str = field(
        default=MediaRegion.GLL, metadata=meta(validate_twilio_media_region)
    )
