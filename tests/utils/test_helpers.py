"""
Tests for utility helper functions
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from envseal.utils.helpers import (
    is_sealed_value,
    find_sealed_values,
    bulk_unseal,
    validate_env_file,
    get_default_env_paths,
    find_env_file,
    auto_unseal_environ,
)
from envseal.core import seal, TOKEN_PREFIX, EnvSealError


class TestHelpers:
    """Test utility helper functions"""

    @pytest.fixture
    def passphrase(self):
        return b"test-passphrase"

    def test_is_sealed_value_true(self):
        """Test detecting sealed values"""
        token = "ENC[v1]:some-encrypted-data"
        assert is_sealed_value(token) is True

    def test_is_sealed_value_false(self):
        """Test non-sealed values"""
        assert is_sealed_value("plain-value") is False
        assert is_sealed_value("") is False
        assert is_sealed_value("ENC[v2]:different-format") is False  # Wrong version

    def test_find_sealed_values(self, passphrase):
        """Test finding sealed values in dictionary"""
        encrypted_token = seal("secret", passphrase)
        data = {
            "plain": "value",
            "encrypted": encrypted_token,
            "another_plain": "another_value",
            "another_encrypted": encrypted_token,
        }

        result = find_sealed_values(data)
        assert set(result) == {"encrypted", "another_encrypted"}

    def test_find_sealed_values_none(self):
        """Test finding sealed values when none exist"""
        data = {"plain1": "value1", "plain2": "value2"}

        result = find_sealed_values(data)
        assert result == []

    def test_bulk_unseal_success(self, passphrase):
        """Test bulk unsealing successful"""
        encrypted_token1 = seal("secret1", passphrase)
        encrypted_token2 = seal("secret2", passphrase)

        data = {
            "VAR1": encrypted_token1,
            "VAR2": "plain-value",
            "VAR3": encrypted_token2,
        }

        result = bulk_unseal(data, passphrase)

        expected = {"VAR1": "secret1", "VAR2": "plain-value", "VAR3": "secret2"}
        assert result == expected

    def test_bulk_unseal_with_errors_skip(self, passphrase):
        """Test bulk unsealing with errors, skipping failures"""
        encrypted_token = seal("secret", passphrase)
        wrong_token = "ENC[v1]:invalid-data"

        data = {"GOOD": encrypted_token, "BAD": wrong_token, "PLAIN": "plain-value"}

        result = bulk_unseal(data, passphrase, skip_errors=True)

        expected = {
            "GOOD": "secret",
            "BAD": wrong_token,  # Unchanged due to error
            "PLAIN": "plain-value",
        }
        assert result == expected

    def test_bulk_unseal_with_errors_no_skip(self, passphrase):
        """Test bulk unsealing with errors, not skipping failures"""
        wrong_token = "ENC[v1]:invalid-data"

        data = {"BAD": wrong_token, "PLAIN": "plain-value"}

        with pytest.raises(EnvSealError):
            bulk_unseal(data, passphrase, skip_errors=False)

    def test_validate_env_file_exists(self):
        """Test validating existing file"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Should not raise
            validate_env_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_validate_env_file_not_exists(self):
        """Test validating non-existent file"""
        with pytest.raises(EnvSealError, match="Environment file not found"):
            validate_env_file(Path("/nonexistent/.env"))

    def test_get_default_env_paths(self):
        """Test getting default environment file paths"""
        paths = get_default_env_paths()
        assert isinstance(paths, list)
        assert all(isinstance(p, Path) for p in paths)
        # Should include common .env file locations
        assert any(".env" in str(p) for p in paths)

    def test_find_env_file_exists(self):
        """Test finding existing env file"""
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as f:
            temp_path = f.name

        try:
            # Mock get_default_env_paths to return our temp file
            with patch(
                "envseal.utils.helpers.get_default_env_paths",
                return_value=[Path(temp_path)],
            ):
                result = find_env_file()
                assert result == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_find_env_file_not_exists(self):
        """Test finding env file when none exist"""
        with patch(
            "envseal.utils.helpers.get_default_env_paths",
            return_value=[Path("/nonexistent/.env")],
        ):
            result = find_env_file()
            assert result is None

    def test_auto_unseal_environ(self, passphrase):
        """Test auto unsealing environment variables"""
        from envseal.core import PassphraseSource

        encrypted_token = seal("secret-value", passphrase)

        # Set up environment
        os.environ["PLAIN_VAR"] = "plain-value"
        os.environ["SECRET_VAR"] = encrypted_token

        original_values = {}
        for var in ["PLAIN_VAR", "SECRET_VAR"]:
            original_values[var] = os.environ[var]

        try:
            result = auto_unseal_environ(
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase=passphrase.decode(),
            )

            assert result["PLAIN_VAR"] == "plain-value"
            assert result["SECRET_VAR"] == "secret-value"

        finally:
            # Restore original values
            for var, value in original_values.items():
                os.environ[var] = value
