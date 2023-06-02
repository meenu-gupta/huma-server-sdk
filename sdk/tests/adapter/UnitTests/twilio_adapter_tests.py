import unittest

from sdk.common.adapter.twilio.twilio_video_config import (
    TwilioVideoAdapterConfig,
    MediaRegion,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

VALID_REGION = MediaRegion.GLL
INVALID_REGION = "random"


class TwilioAdapterTestCase(unittest.TestCase):
    @staticmethod
    def get_data(valid=True):
        media_region = VALID_REGION if valid else INVALID_REGION
        data = {
            TwilioVideoAdapterConfig.ACCOUNT_SID: "accountSid",
            TwilioVideoAdapterConfig.AUTH_TOKEN: "authToken",
            TwilioVideoAdapterConfig.API_KEY: "apiKey",
            TwilioVideoAdapterConfig.API_SECRET: "apiSecret",
            TwilioVideoAdapterConfig.MEDIA_REGION: media_region,
        }
        return data

    def test_media_region_valid_region(self):
        valid_data = self.get_data(valid=True)
        try:
            TwilioVideoAdapterConfig.from_dict(valid_data)
        except Exception:
            self.fail("Invalid data provided")

    def test_media_region_invalid_region(self):
        invalid_data = self.get_data(valid=False)
        with self.assertRaises(ConvertibleClassValidationError):
            TwilioVideoAdapterConfig.from_dict(invalid_data)
