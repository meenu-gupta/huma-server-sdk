import unittest
from unittest import TestCase

from cryptography.fernet import InvalidToken

from sdk.common.utils.encryption_utils import generate_key, encrypt, decrypt


class TestEncryption(TestCase):
    def test_encrypt_decrypt_correctly(self):
        key = generate_key()
        self.assertEqual(decrypt(encrypt("test me", key), key), "test me")

    def test_encrypt_different_decrypt(self):
        with self.assertRaises(InvalidToken):
            key = generate_key()
            key1 = generate_key()
            decrypt(encrypt("test me", key), key1)


if __name__ == "__main__":
    unittest.main()
