import unittest

from sdk.auth.events.mfa_required_event import MFARequiredEvent

SAMPLE_ID = "600a8476a961574fb38157d5"


class MFARequiredEventTestCase(unittest.TestCase):
    def test_success_event_init(self):
        event = MFARequiredEvent(user_id=SAMPLE_ID)
        self.assertEqual(event.user_id, SAMPLE_ID)


if __name__ == "__main__":
    unittest.main()
