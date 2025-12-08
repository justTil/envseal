"""
Tests for core encryption functionality
"""

import pytest
from envseal.core import seal, unseal, _kdf, TOKEN_PREFIX, EnvSealError


class TestEncryption:
    """Test core encryption/decryption functions"""

    @pytest.fixture
    def passphrase(self):
        return b"test-passphrase"

    def test_kdf_derives_key(self):
        """Test that KDF produces consistent keys"""
        passphrase = b"test-passphrase"
        salt = b"test-salt123456789012"  # 16 bytes

        key1 = _kdf(passphrase, salt)
        key2 = _kdf(passphrase, salt)

        assert key1 == key2
        assert len(key1) == 32  # AES-256 key length

    def test_kdf_different_salt_different_key(self):
        """Test that different salts produce different keys"""
        passphrase = b"test-passphrase"
        salt1 = b"salt1-12345678901"
        salt2 = b"salt2-12345678901"

        key1 = _kdf(passphrase, salt1)
        key2 = _kdf(passphrase, salt2)

        assert key1 != key2

    def test_seal_returns_token_format(self, passphrase):
        """Test that seal returns properly formatted token"""
        plaintext = "test-secret"
        token = seal(plaintext, passphrase)

        assert isinstance(token, str)
        assert token.startswith(TOKEN_PREFIX)

    def test_seal_unseal_roundtrip(self, passphrase):
        """Test that seal/unseal preserves data"""
        plaintext = "test-secret-value"
        token = seal(plaintext, passphrase)
        decrypted = unseal(token, passphrase)

        assert decrypted.decode() == plaintext

    def test_seal_unseal_bytes(self, passphrase):
        """Test seal/unseal with bytes input"""
        plaintext_bytes = b"test-secret-bytes"
        token = seal(plaintext_bytes, passphrase)
        decrypted = unseal(token, passphrase)

        assert decrypted == plaintext_bytes

    def test_unseal_wrong_passphrase_fails(self, passphrase):
        """Test that unseal fails with wrong passphrase"""
        plaintext = "test-secret"
        token = seal(plaintext, passphrase)
        wrong_passphrase = b"wrong-passphrase"

        with pytest.raises(EnvSealError, match="Decryption failed"):
            unseal(token, wrong_passphrase)

    def test_unseal_invalid_token_fails(self, passphrase):
        """Test that unseal fails with invalid token"""
        with pytest.raises(EnvSealError):
            unseal("invalid-token", passphrase)

    def test_unseal_malformed_token_fails(self, passphrase):
        """Test that unseal fails with malformed token"""
        with pytest.raises(EnvSealError):
            unseal("ENC[v1]:invalid-base64", passphrase)

    def test_seal_empty_string(self, passphrase):
        """Test sealing empty string"""
        token = seal("", passphrase)
        decrypted = unseal(token, passphrase)

        assert decrypted.decode() == ""

    def test_seal_unicode_string(self, passphrase):
        """Test sealing unicode string"""
        plaintext = "héllo wörld 🌍"
        token = seal(plaintext, passphrase)
        decrypted = unseal(token, passphrase)

        assert decrypted.decode() == plaintext
