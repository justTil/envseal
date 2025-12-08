"""
Tests for core environment operation functionality
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from envseal.core import load_sealed_env, apply_sealed_env, seal, EnvSealError


class TestEnvOperations:
    """Test core environment operations"""

    @pytest.fixture
    def passphrase(self):
        return b"test-passphrase"

    def test_load_sealed_env_basic(self, passphrase):
        """Test basic loading of sealed environment variables"""
        # Create temporary .env file
        encrypted_token = seal("secret-value", passphrase)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("PLAIN_VAR=plain-value\n")
            f.write(f"SECRET_VAR={encrypted_token}\n")
            f.write("ANOTHER_SECRET=another-value\n")
            env_path = f.name

        try:
            from envseal.core import PassphraseSource

            result = load_sealed_env(
                dotenv_path=Path(env_path),
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
            )

            expected = {
                "PLAIN_VAR": "plain-value",
                "SECRET_VAR": "secret-value",
                "ANOTHER_SECRET": "another-value",
            }
            assert result == expected

        finally:
            os.unlink(env_path)

    def test_load_sealed_env_no_file(self, passphrase):
        """Test loading when no .env file exists"""
        # Create a temp directory and explicitly point to a non-existent file there
        # This avoids python-dotenv finding .env files in parent directories
        from envseal.core import PassphraseSource
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_env = Path(tmpdir) / "nonexistent.env"
            result = load_sealed_env(
                dotenv_path=nonexistent_env,
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
            )
            # Should return empty dict when file doesn't exist
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_load_sealed_env_file_not_found(self, passphrase):
        """Test loading from non-existent file"""
        # The actual function doesn't check for file existence, just returns empty dict
        # when dotenv_values() doesn't find the file
        from envseal.core import PassphraseSource

        result = load_sealed_env(
            dotenv_path=Path("/nonexistent/.env"),
            passphrase_source=PassphraseSource.HARDCODED,
            hardcoded_passphrase=passphrase.decode(),
        )
        assert isinstance(result, dict)

    def test_load_sealed_env_with_override(self, passphrase):
        """Test loading with override behavior"""
        # load_sealed_env just returns a dict, doesn't check os.environ
        # The override logic is in apply_sealed_env
        encrypted_token = seal("new-secret", passphrase)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"EXISTING_VAR={encrypted_token}\n")
            f.write("NEW_VAR=new-value\n")
            env_path = f.name

        try:
            from envseal.core import PassphraseSource

            result = load_sealed_env(
                dotenv_path=Path(env_path),
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
            )
            assert result["EXISTING_VAR"] == "new-secret"
            assert result["NEW_VAR"] == "new-value"

        finally:
            os.unlink(env_path)

    def test_apply_sealed_env_basic(self, passphrase):
        """Test applying sealed environment variables"""
        # Create temp file with env vars
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR1=value1\n")
            f.write("TEST_VAR2=value2\n")
            env_path = f.name

        # Clear any existing values
        original_values = {}
        for var in ["TEST_VAR1", "TEST_VAR2"]:
            if var in os.environ:
                original_values[var] = os.environ[var]
                del os.environ[var]

        try:
            from envseal.core import PassphraseSource

            apply_sealed_env(
                dotenv_path=Path(env_path),
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
            )

            # Check variables were set
            assert os.environ["TEST_VAR1"] == "value1"
            assert os.environ["TEST_VAR2"] == "value2"

        finally:
            # Cleanup
            os.unlink(env_path)
            for var in ["TEST_VAR1", "TEST_VAR2"]:
                if var in os.environ:
                    del os.environ[var]
                if var in original_values:
                    os.environ[var] = original_values[var]

    def test_apply_sealed_env_with_override(self, passphrase):
        """Test applying with override behavior"""
        # Set up existing environment
        os.environ["EXISTING_VAR"] = "original-value"
        os.environ["NEW_VAR"] = "should-not-be-overridden"

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("EXISTING_VAR=new-value\n")
            f.write("NEW_VAR=updated-value\n")
            env_path = f.name

        try:
            from envseal.core import PassphraseSource

            # Test without override
            apply_sealed_env(
                dotenv_path=Path(env_path),
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
                override=False,
            )
            assert os.environ["EXISTING_VAR"] == "original-value"  # Not overridden
            assert os.environ["NEW_VAR"] == "should-not-be-overridden"  # Not overridden

            # Reset and test with override
            apply_sealed_env(
                dotenv_path=Path(env_path),
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
                override=True,
            )
            assert os.environ["EXISTING_VAR"] == "new-value"  # Overridden
            assert os.environ["NEW_VAR"] == "updated-value"  # Overridden

        finally:
            # Cleanup
            os.unlink(env_path)
            for var in ["EXISTING_VAR", "NEW_VAR"]:
                if var in os.environ:
                    del os.environ[var]

    def test_load_sealed_env_malformed_token(self, passphrase):
        """Test loading env with malformed encrypted token"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("MALFORMED=ENC[v1]:invalid-base64\n")
            env_path = f.name

        try:
            from envseal.core import PassphraseSource

            with pytest.raises(EnvSealError, match="Failed to unseal"):
                load_sealed_env(
                    dotenv_path=Path(env_path),
                    passphrase_source=PassphraseSource.HARDCODED,
                    hardcoded_passphrase=passphrase.decode(),
                )

        finally:
            os.unlink(env_path)

    def test_load_sealed_env_wrong_passphrase(self, passphrase):
        """Test loading env with wrong passphrase"""
        encrypted_token = seal("secret", passphrase)
        wrong_passphrase = "wrong-pass"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"SECRET={encrypted_token}\n")
            env_path = f.name

        try:
            from envseal.core import PassphraseSource

            with pytest.raises(EnvSealError, match="Failed to unseal"):
                load_sealed_env(
                    dotenv_path=Path(env_path),
                    passphrase_source=PassphraseSource.HARDCODED,
                    hardcoded_passphrase=wrong_passphrase,
                )

        finally:
            os.unlink(env_path)
