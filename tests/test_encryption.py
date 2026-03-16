                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            import unittest
from src.core.encryption import EncryptionService

class TestEncryptionService(unittest.TestCase):

    def setUp(self):
        self.encryption_service = EncryptionService()
        self.test_password = "securepassword"
        self.test_data = "This is a test note."

    def test_key_derivation(self):
<<<<<<< HEAD
        key, salt = self.encryption_service.derive_key(self.test_password)
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # AES-256 key size
        self.assertEqual(len(salt), 16)  # Salt size
=======
        key = self.encryption_service.derive_key(self.test_password)
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # Assuming AES-256 key size
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d

    def test_encryption_decryption(self):
        encrypted_data = self.encryption_service.encrypt(self.test_data, self.test_password)
        decrypted_data = self.encryption_service.decrypt(encrypted_data, self.test_password)
        self.assertEqual(decrypted_data, self.test_data)

    def test_encryption_with_different_passwords(self):
        encrypted_data = self.encryption_service.encrypt(self.test_data, self.test_password)
        different_password = "differentpassword"
<<<<<<< HEAD
        with self.assertRaises(ValueError):
            self.encryption_service.decrypt(encrypted_data, different_password)
=======
        decrypted_data = self.encryption_service.decrypt(encrypted_data, different_password)
        self.assertNotEqual(decrypted_data, self.test_data)
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d

    def test_invalid_decryption(self):
        with self.assertRaises(ValueError):
            self.encryption_service.decrypt(b"invaliddata", self.test_password)

if __name__ == '__main__':
    unittest.main()