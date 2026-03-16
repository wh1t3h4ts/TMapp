                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            import unittest
from src.core.encryption import EncryptionService

class TestEncryptionService(unittest.TestCase):

    def setUp(self):
        self.encryption_service = EncryptionService()
        self.test_password = "securepassword"
        self.test_data = "This is a test note."

    def test_key_derivation(self):
        key, salt = self.encryption_service.derive_key(self.test_password)
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # AES-256 key size
        self.assertEqual(len(salt), 16)  # Salt size

    def test_encryption_decryption(self):
        encrypted_data = self.encryption_service.encrypt(self.test_data, self.test_password)
        decrypted_data = self.encryption_service.decrypt(encrypted_data, self.test_password)
        self.assertEqual(decrypted_data, self.test_data)

    def test_encryption_with_different_passwords(self):
        encrypted_data = self.encryption_service.encrypt(self.test_data, self.test_password)
        different_password = "differentpassword"
        with self.assertRaises(ValueError):
            self.encryption_service.decrypt(encrypted_data, different_password)

    def test_invalid_decryption(self):
        with self.assertRaises(ValueError):
            self.encryption_service.decrypt(b"invaliddata", self.test_password)

if __name__ == '__main__':
    unittest.main()