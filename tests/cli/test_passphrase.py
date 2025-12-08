"""
Tests for CLI passphrase handling functionality
"""

import os
import pytest

from envseal.cli import get_passphrase_from_args
from envseal.core import EnvSealError


class TestGetPassphraseFromArgs:
    """Test passphrase extraction from CLI arguments"""

    def test_hardcoded_passphrase_args(self):
        """Test extracting hardcoded passphrase from args"""
        args = type(
            "Args",
            (),
            {
                "passphrase_source": "hardcoded",
                "hardcoded_passphrase": "test-passphrase",
                "env_var": "ENVSEAL_PASSPHRASE",
                "dotenv_file": None,
                "dotenv_var": "ENVSEAL_PASSPHRASE",
            },
        )()

        result = get_passphrase_from_args(args)
        assert result == b"test-passphrase"

    def test_env_var_passphrase_args(self):
        """Test extracting environment variable passphrase from args"""
        var_name = "TEST_CLI_PASSPHRASE"
        test_passphrase = "cli-test-passphrase"

        os.environ[var_name] = test_passphrase
        try:
            args = type(
                "Args",
                (),
                {
                    "passphrase_source": "env_var",
                    "hardcoded_passphrase": None,
                    "env_var": var_name,
                    "dotenv_file": None,
                    "dotenv_var": "ENVSEAL_PASSPHRASE",
                },
            )()

            result = get_passphrase_from_args(args)
            assert result == test_passphrase.encode()
        finally:
            del os.environ[var_name]

    def test_dotenv_passphrase_args(self):
        """Test extracting dotenv passphrase from args"""
        # This would require setting up a temp .env file
        # For now, test the structure
        args = type(
            "Args",
            (),
            {
                "passphrase_source": "dotenv",
                "hardcoded_passphrase": None,
                "env_var": "ENVSEAL_PASSPHRASE",
                "dotenv_file": "/tmp/test.env",
                "dotenv_var": "MY_PASSPHRASE",
            },
        )()

        # This will fail because the file doesn't exist, but tests the call structure
        with pytest.raises(EnvSealError):
            get_passphrase_from_args(args)
