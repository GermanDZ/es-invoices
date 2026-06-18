"""Unit tests for certificates.crypto (T-011 Operation 2).

Covers the encryption-at-rest primitive that requirement 2 depends on:
round-trip fidelity, per-call nonce freshness, and that a wrong key or tampered
ciphertext fails loudly rather than returning garbage.
"""
import base64
import os

from cryptography.exceptions import InvalidTag
from django.test import SimpleTestCase, override_settings

from certificates import crypto

KEY_A = crypto.generate_key()
KEY_B = crypto.generate_key()


@override_settings(CERT_ENCRYPTION_KEY=KEY_A)
class EncryptDecryptTests(SimpleTestCase):
    def test_roundtrip_recovers_plaintext(self):
        plaintext = b"qualified-cert-bytes\x00\x01\x02"
        nonce, ciphertext = crypto.encrypt(plaintext)
        self.assertEqual(crypto.decrypt(nonce, ciphertext), plaintext)

    def test_ciphertext_differs_from_plaintext(self):
        plaintext = b"sensitive passphrase"
        _, ciphertext = crypto.encrypt(plaintext)
        self.assertNotIn(plaintext, ciphertext)

    def test_fresh_nonce_per_call(self):
        plaintext = b"same input"
        nonce1, ct1 = crypto.encrypt(plaintext)
        nonce2, ct2 = crypto.encrypt(plaintext)
        self.assertNotEqual(nonce1, nonce2)
        self.assertNotEqual(ct1, ct2)  # GCM is randomized via the nonce

    def test_tampered_ciphertext_raises(self):
        nonce, ciphertext = crypto.encrypt(b"payload")
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF
        with self.assertRaises(InvalidTag):
            crypto.decrypt(nonce, bytes(tampered))

    def test_non_bytes_plaintext_rejected(self):
        with self.assertRaises(TypeError):
            crypto.encrypt("a string is not bytes")  # type: ignore[arg-type]


class WrongKeyTests(SimpleTestCase):
    def test_decrypt_with_different_key_raises(self):
        with override_settings(CERT_ENCRYPTION_KEY=KEY_A):
            nonce, ciphertext = crypto.encrypt(b"secret")
        with override_settings(CERT_ENCRYPTION_KEY=KEY_B):
            with self.assertRaises(InvalidTag):
                crypto.decrypt(nonce, ciphertext)


class KeyConfigTests(SimpleTestCase):
    @override_settings(CERT_ENCRYPTION_KEY=None)
    def test_missing_key_raises(self):
        with self.assertRaises(crypto.EncryptionKeyError):
            crypto.encrypt(b"x")

    @override_settings(CERT_ENCRYPTION_KEY="not!base64!")
    def test_malformed_key_raises(self):
        with self.assertRaises(crypto.EncryptionKeyError):
            crypto.encrypt(b"x")

    @override_settings(CERT_ENCRYPTION_KEY=base64.b64encode(os.urandom(16)).decode())
    def test_wrong_length_key_raises(self):
        # 16 bytes decoded -> not AES-256.
        with self.assertRaises(crypto.EncryptionKeyError):
            crypto.encrypt(b"x")

    def test_generate_key_is_32_bytes_base64(self):
        key = crypto.generate_key()
        self.assertEqual(len(base64.b64decode(key)), 32)
