import unittest
from src.core.security import encrypt_secret, decrypt_secret, DecryptionError

class TestSecurity(unittest.TestCase):
    def test_encrypt_decrypt_success(self):
        test_secret = "my_super_secret_key_123"
        encrypted = encrypt_secret(test_secret)
        self.assertNotEqual(test_secret, encrypted)
        
        decrypted = decrypt_secret(encrypted)
        self.assertEqual(test_secret, decrypted)

    def test_decrypt_failure_raises_exception(self):
        # Passing an invalid encrypted string should raise DecryptionError
        with self.assertRaises(DecryptionError):
            decrypt_secret("invalid_encrypted_ciphertext_string_12345")

    def test_empty_string(self):
        self.assertEqual(encrypt_secret(""), "")
        self.assertEqual(decrypt_secret(""), "")

if __name__ == "__main__":
    unittest.main()
