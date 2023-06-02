import unittest

from sdk.common.utils.hash_utils import hash_new_password, is_correct_password


class CheckHashedPasswordTestCase(unittest.TestCase):
    PASSWORD = "ThisISPassword123"
    WRONG_PASSWORD = "ThisIsNotPassword123"

    def test_correct_password(self):
        pw_hash = hash_new_password(self.PASSWORD)
        self.assertTrue(is_correct_password(pw_hash, self.PASSWORD))

    def test_incorrect_password(self):
        pw_hash = hash_new_password(self.PASSWORD)
        self.assertFalse(is_correct_password(pw_hash, self.WRONG_PASSWORD))

    def test_incorrect_argument_type(self):
        pw_hash = None
        password = self.PASSWORD
        self.assertFalse(is_correct_password(pw_hash, password))


if __name__ == "__main__":
    unittest.main()
