import unittest

from extensions.twilio_video.router.twilio_video_request import (
    StartVideoCallRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "600a8476a961574fb38157d5"


class StartVideoCallRequestObjectTestCase(unittest.TestCase):
    def test_success_init_valid_fields(self):
        try:
            StartVideoCallRequestObject.from_dict(
                {
                    StartVideoCallRequestObject.USER_ID: SAMPLE_ID,
                    StartVideoCallRequestObject.MANAGER_ID: SAMPLE_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            StartVideoCallRequestObject.from_dict(
                {StartVideoCallRequestObject.MANAGER_ID: SAMPLE_ID}
            )

    def test_failure_no_manager_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            StartVideoCallRequestObject.from_dict(
                {
                    StartVideoCallRequestObject.USER_ID: SAMPLE_ID,
                }
            )


if __name__ == "__main__":
    unittest.main()
