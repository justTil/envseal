"""
Tests for envseal.core
"""

import os
import tempfile
import pytest
from pathlib import Path

from envseal.core import (
    seal,
    unseal,
    get_passphrase,
    store_passphrase_in_keyring,
    load_sealed_env,
    apply_sealed_env,
    PassphraseSource,
    EnvSealError,
    TOKEN_PREFIX,
)


class TestSealUnseal:
    """Test basic seal/unseal functionality"""

    def test_seal_unseal_string(self):
        """Test sealing and unsealing a string"""
        passphrase = b"test-passphrase"
        plaintext = "hello world"

        token = seal(plaintext, passphrase)
        assert token.startswith(TOKEN_PREFIX)

        decrypted = unseal(token, passphrase)
        assert decrypted.decode() == plaintext

    def test_seal_unseal_bytes(self):
        """Test sealing and unsealing bytes"""
        passphrase = b"test-passphrase"
        plaintext = b"hello world"

        token = seal(plaintext, passphrase)
        decrypted = unseal(token, passphrase)
        assert decrypted == plaintext

    def test_wrong_passphrase(self):
        """Test that wrong passphrase fails"""
        passphrase1 = b"correct-passphrase"
        passphrase2 = b"wrong-passphrase"
        plaintext = "secret data"

        token = seal(plaintext, passphrase1)

        with pytest.raises(EnvSealError, match="Decryption failed"):
            unseal(token, passphrase2)

    def test_invalid_token_format(self):
        """Test that invalid token format raises error"""
        passphrase = b"test-passphrase"

        with pytest.raises(EnvSealError, match="Invalid token format"):
            unseal("invalid-token", passphrase)

    def test_malformed_token(self):
        """Test that malformed token raises error"""
        passphrase = b"test-passphrase"

        with pytest.raises(EnvSealError, match="Malformed token"):
            unseal(f"{TOKEN_PREFIX}invalid-base64", passphrase)


class TestGetPassphrase:
    """Test passphrase retrieval from different sources"""

    def test_hardcoded_passphrase(self):
        """Test hardcoded passphrase source"""
        expected = "test-passphrase"
        result = get_passphrase(
            PassphraseSource.HARDCODED, hardcoded_passphrase=expected
        )
        assert result == expected.encode()

    def test_env_var_passphrase(self):
        """Test environment variable passphrase source"""
        var_name = "TEST_ENVSEAL_PASSPHRASE"
        expected = "env-var-passphrase"

        os.environ[var_name] = expected
        try:
            result = get_passphrase(PassphraseSource.ENV_VAR, env_var_name=var_name)
            assert result == expected.encode()
        finally:
            del os.environ[var_name]

    def test_env_var_missing(self):
        """Test missing environment variable"""
        with pytest.raises(EnvSealError, match="Environment variable .* not found"):
            get_passphrase(PassphraseSource.ENV_VAR, env_var_name="NONEXISTENT_VAR")

    def test_hardcoded_missing(self):
        """Test missing hardcoded passphrase"""
        with pytest.raises(EnvSealError, match="hardcoded_passphrase must be provided"):
            get_passphrase(PassphraseSource.HARDCODED)


class TestDotenvIntegration:
    """Test .env file integration"""

    def test_load_sealed_env(self):
        """Test loading and decrypting .env file"""
        passphrase = b"test-passphrase"

        # Create encrypted values
        secret1 = seal("secret-value-1", passphrase)
        secret2 = seal("secret-value-2", passphrase)

        # Create temp .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"PLAIN_VAR=plain-value\n")
            f.write(f"SECRET1={secret1}\n")
            f.write(f"SECRET2={secret2}\n")
            f.write(f"EMPTY_VAR=\n")
            env_path = f.name

        try:
            # Load with decryption
            env_vars = load_sealed_env(
                dotenv_path=env_path,
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase="test-passphrase",
            )

            assert env_vars["PLAIN_VAR"] == "plain-value"
            assert env_vars["SECRET1"] == "secret-value-1"
            assert env_vars["SECRET2"] == "secret-value-2"
            assert env_vars["EMPTY_VAR"] == ""

        finally:
            os.unlink(env_path)

    def test_apply_sealed_env(self):
        """Test applying sealed environment variables"""
        passphrase = b"test-passphrase"
        secret_value = seal("secret-database-password", passphrase)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"TEST_DB_PASSWORD={secret_value}\n")
            f.write(f"TEST_PLAIN_VAR=plain-value\n")
            env_path = f.name

        # Clear any existing values
        test_vars = ["TEST_DB_PASSWORD", "TEST_PLAIN_VAR"]
        original_values = {}
        for var in test_vars:
            if var in os.environ:
                original_values[var] = os.environ[var]
                del os.environ[var]

        try:
            apply_sealed_env(
                dotenv_path=env_path,
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase="test-passphrase",
            )

            assert os.environ["TEST_DB_PASSWORD"] == "secret-database-password"
            assert os.environ["TEST_PLAIN_VAR"] == "plain-value"

        finally:
            # Cleanup
            for var in test_vars:
                if var in os.environ:
                    del os.environ[var]
                if var in original_values:
                    os.environ[var] = original_values[var]
            os.unlink(env_path)


class TestErrorHandling:
    """Test error conditions and edge cases"""

    def test_unseal_decryption_error(self):
        """Test decryption error with wrong passphrase"""
        passphrase1 = b"passphrase1"
        passphrase2 = b"passphrase2"

        token = seal("test", passphrase1)

        with pytest.raises(EnvSealError, match="Decryption failed"):
            unseal(token, passphrase2)

    def test_load_sealed_env_decryption_error(self):
        """Test error handling in load_sealed_env"""
        passphrase1 = b"passphrase1"
        passphrase2 = b"passphrase2"

        # Create encrypted value with one passphrase
        secret = seal("secret-value", passphrase1)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"SECRET_VAR={secret}\n")
            env_path = f.name

        try:
            # Try to decrypt with wrong passphrase
            with pytest.raises(EnvSealError, match="Failed to unseal SECRET_VAR"):
                load_sealed_env(
                    dotenv_path=env_path,
                    passphrase_source=PassphraseSource.HARDCODED,
                    hardcoded_passphrase="wrong-passphrase",
                )
        finally:
            os.unlink(env_path)


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_complete_workflow(self):
        """Test complete encrypt -> store -> load workflow"""
        # Step 1: Encrypt some secrets
        passphrase = "my-master-passphrase"
        db_password = "super-secret-db-password"
        api_key = "sk-1234567890abcdef"

        passphrase_bytes = passphrase.encode()
        encrypted_db = seal(db_password, passphrase_bytes)
        encrypted_api = seal(api_key, passphrase_bytes)

        # Step 2: Create .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"APP_NAME=MyApp\n")
            f.write(f"DB_PASSWORD={encrypted_db}\n")
            f.write(f"API_KEY={encrypted_api}\n")
            f.write(f"DEBUG=true\n")
            env_path = f.name

        # Step 3: Load and verify
        try:
            env_vars = load_sealed_env(
                dotenv_path=env_path,
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase,
            )

            assert env_vars["APP_NAME"] == "MyApp"
            assert env_vars["DB_PASSWORD"] == db_password
            assert env_vars["API_KEY"] == api_key
            assert env_vars["DEBUG"] == "true"

        finally:
            os.unlink(env_path)
