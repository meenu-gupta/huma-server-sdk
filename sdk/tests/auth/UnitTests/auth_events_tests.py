import unittest

from sdk.auth.events.sign_in_event import SignInEvent

SAMPLE_ID = "600a8476a961574fb38157d5"


class SignInEventTestCase(unittest.TestCase):
    def test_success_event_init(self):
        event = SignInEvent(user_id=SAMPLE_ID)
        self.assertEqual(event.user_id, SAMPLE_ID)


if __name__ == "__main__":
    unittest.main()
