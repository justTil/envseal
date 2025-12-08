"""
Tests for core passphrase handling functionality
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from envseal.core import (
    get_passphrase,
    store_passphrase_in_keyring,
    PassphraseSource,
    EnvSealError,
    APP_NAME,
    KEY_ALIAS,
)


class TestPassphraseCore:
    """Test core passphrase functions"""

    def test_get_passphrase_keyring(self):
        """Test getting passphrase from keyring"""
        with patch(
            "envseal.core.keyring.get_password", return_value="keyring-passphrase"
        ) as mock_get:
            result = get_passphrase(PassphraseSource.KEYRING)
            assert result == b"keyring-passphrase"
            mock_get.assert_called_once_with(APP_NAME, KEY_ALIAS)

    def test_get_passphrase_keyring_not_found(self):
        """Test keyring passphrase not found"""
        with patch("envseal.core.keyring.get_password", return_value=None):
            with pytest.raises(EnvSealError, match="No passphrase found in keyring"):
                get_passphrase(PassphraseSource.KEYRING)

    def test_get_passphrase_hardcoded(self):
        """Test hardcoded passphrase"""
        passphrase = "hardcoded-pass"
        result = get_passphrase(
            PassphraseSource.HARDCODED, hardcoded_passphrase=passphrase
        )
        assert result == passphrase.encode()

    def test_get_passphrase_env_var(self):
        """Test environment variable passphrase"""
        var_name = "TEST_PASSPHRASE_VAR"
        test_passphrase = "env-var-passphrase"

        os.environ[var_name] = test_passphrase
        try:
            result = get_passphrase(PassphraseSource.ENV_VAR, env_var_name=var_name)
            assert result == test_passphrase.encode()
        finally:
            del os.environ[var_name]

    def test_get_passphrase_env_var_not_found(self):
        """Test environment variable not found"""
        with pytest.raises(
            EnvSealError, match="Environment variable NONEXISTENT_VAR not found"
        ):
            get_passphrase(PassphraseSource.ENV_VAR, env_var_name="NONEXISTENT_VAR")

    def test_get_passphrase_dotenv(self):
        """Test dotenv passphrase"""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("MY_PASSPHRASE=test-dotenv-pass\n")
            env_path = f.name

        try:
            result = get_passphrase(
                PassphraseSource.DOTENV,
                dotenv_path=env_path,
                dotenv_var_name="MY_PASSPHRASE",
            )
            assert result == b"test-dotenv-pass"
        finally:
            os.unlink(env_path)

    def test_get_passphrase_dotenv_file_not_found(self):
        """Test dotenv file not found"""
        with pytest.raises(
            EnvSealError, match="Variable ENVSEAL_PASSPHRASE not found in .env file"
        ):
            get_passphrase(PassphraseSource.DOTENV, dotenv_path="/nonexistent/.env")

    def test_get_passphrase_dotenv_var_not_found(self):
        """Test dotenv variable not found"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("OTHER_VAR=value\n")
            env_path = f.name

        try:
            with pytest.raises(
                EnvSealError, match="Variable MISSING_VAR not found in .env file"
            ):
                get_passphrase(
                    PassphraseSource.DOTENV,
                    dotenv_path=env_path,
                    dotenv_var_name="MISSING_VAR",
                )
        finally:
            os.unlink(env_path)

    @patch("envseal.core.getpass.getpass")
    def test_get_passphrase_prompt(self, mock_getpass):
        """Test prompt passphrase"""
        mock_getpass.return_value = "prompted-passphrase"
        result = get_passphrase(PassphraseSource.PROMPT)
        assert result == b"prompted-passphrase"
        mock_getpass.assert_called_once()

    def test_store_passphrase_in_keyring(self):
        """Test storing passphrase in keyring"""
        with patch("envseal.core.keyring.set_password") as mock_set:
            store_passphrase_in_keyring("test-passphrase")
            mock_set.assert_called_once_with(APP_NAME, KEY_ALIAS, "test-passphrase")

    def test_store_passphrase_in_keyring_custom_app(self):
        """Test storing passphrase with custom app name"""
        with patch("envseal.core.keyring.set_password") as mock_set:
            store_passphrase_in_keyring(
                "test-passphrase", app_name="custom-app", key_alias="custom-key"
            )
            mock_set.assert_called_once_with(
                "custom-app", "custom-key", "test-passphrase"
            )
