"""
Tests for CLI command functions
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from envseal.cli import (
    cmd_seal,
    cmd_unseal,
    cmd_store_passphrase,
    cmd_load_env,
    cmd_seal_file,
    cmd_unseal_file,
)
from envseal.core import seal, EnvSealError


class TestCLICommands:
    """Test individual CLI command functions"""

    @pytest.fixture
    def passphrase(self):
        return b"test-passphrase"

    def test_cmd_seal_success(self, passphrase, capsys):
        """Test successful seal command"""
        test_value = "test-secret"
        args = type("Args", (), {"value": test_value})()

        with patch("envseal.cli.get_passphrase_from_args", return_value=passphrase):
            cmd_seal(args)

            captured = capsys.readouterr()
            assert captured.out.strip().startswith("ENC[v1]:")
            assert captured.err == ""

    def test_cmd_seal_error(self, capsys):
        """Test seal command with error"""
        args = type("Args", (), {"value": "test"})()

        with patch(
            "envseal.cli.get_passphrase_from_args",
            side_effect=EnvSealError("Test error"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                cmd_seal(args)

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Error: Test error" in captured.err

    def test_cmd_unseal_success(self, passphrase, capsys):
        """Test successful unseal command"""
        plaintext = "test-secret"
        token = seal(plaintext, passphrase)

        args = type("Args", (), {"token": token})()

        with patch("envseal.cli.get_passphrase_from_args", return_value=passphrase):
            cmd_unseal(args)

            captured = capsys.readouterr()
            assert captured.out.strip() == plaintext
            assert captured.err == ""

    def test_cmd_unseal_error(self, capsys):
        """Test unseal command with error"""
        args = type("Args", (), {"token": "invalid-token"})()

        with patch(
            "envseal.cli.get_passphrase_from_args",
            side_effect=EnvSealError("Test error"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                cmd_unseal(args)

            assert exc_info.value.code == 1

    @patch("envseal.cli.store_passphrase_in_keyring")
    def test_cmd_store_passphrase_success(self, mock_store, capsys):
        """Test successful store-passphrase command"""
        args = type(
            "Args",
            (),
            {
                "passphrase": "my-passphrase",
                "app_name": "test-app",
                "key_alias": "test-key",
            },
        )()

        cmd_store_passphrase(args)

        mock_store.assert_called_once_with(
            "my-passphrase", app_name="test-app", key_alias="test-key"
        )
        captured = capsys.readouterr()
        assert "Passphrase stored in keyring for test-app:test-key" in captured.out

    @patch("envseal.cli.store_passphrase_in_keyring")
    def test_cmd_store_passphrase_error(self, mock_store, capsys):
        """Test store-passphrase command with error"""
        mock_store.side_effect = EnvSealError("Storage failed")

        args = type(
            "Args", (), {"passphrase": "test", "app_name": "app", "key_alias": "key"}
        )()

        with pytest.raises(SystemExit) as exc_info:
            cmd_store_passphrase(args)

        assert exc_info.value.code == 1

    def test_cmd_load_env_display_mode(self, capsys):
        """Test load-env command in display mode"""
        env_vars = {"VAR1": "value1", "VAR2": "value2"}

        args = type(
            "Args",
            (),
            {
                "env_file": None,
                "apply": False,
                "override": False,
                "passphrase_source": "hardcoded",
                "hardcoded_passphrase": "test",
                "env_var": "ENVSEAL_PASSPHRASE",
                "dotenv_file": None,
                "dotenv_var": "ENVSEAL_PASSPHRASE",
            },
        )()

        with patch("envseal.cli.load_sealed_env", return_value=env_vars):
            cmd_load_env(args)

            captured = capsys.readouterr()
            output_lines = captured.out.strip().split("\n")
            assert "VAR1=value1" in output_lines
            assert "VAR2=value2" in output_lines

    def test_cmd_load_env_apply_mode(self, capsys):
        """Test load-env command in apply mode"""
        args = type(
            "Args",
            (),
            {
                "env_file": "/tmp/test.env",
                "apply": True,
                "override": False,
                "passphrase_source": "hardcoded",
                "hardcoded_passphrase": "test",
                "env_var": "ENVSEAL_PASSPHRASE",
                "dotenv_file": None,
                "dotenv_var": "ENVSEAL_PASSPHRASE",
            },
        )()

        with patch("envseal.cli.apply_sealed_env") as mock_apply:
            cmd_load_env(args)

            mock_apply.assert_called_once()
            captured = capsys.readouterr()
            assert "Environment variables loaded and applied" in captured.out

    def test_cmd_load_env_error(self, capsys):
        """Test load-env command with error"""
        args = type(
            "Args",
            (),
            {
                "env_file": None,
                "apply": False,
                "override": False,
                "passphrase_source": "hardcoded",
                "hardcoded_passphrase": "test",
                "env_var": "ENVSEAL_PASSPHRASE",
                "dotenv_file": None,
                "dotenv_var": "ENVSEAL_PASSPHRASE",
            },
        )()

        with patch(
            "envseal.cli.load_sealed_env", side_effect=EnvSealError("Load failed")
        ):
            with pytest.raises(SystemExit) as exc_info:
                cmd_load_env(args)

            assert exc_info.value.code == 1

    @pytest.fixture
    def temp_env_file(self):
        """Create a temporary .env file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    def test_cmd_seal_file_success(self, temp_env_file, capsys):
        """Test successful seal-file command"""
        # Create test file
        with open(temp_env_file, "w") as f:
            f.write("SECRET=test-value\n")

        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": False,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.seal_file", return_value=1) as mock_seal:
                cmd_seal_file(args)

                mock_seal.assert_called_once()
                captured = capsys.readouterr()
                assert "Successfully encrypted 1 value(s)" in captured.out

    def test_cmd_seal_file_no_changes(self, temp_env_file, capsys):
        """Test seal-file with no changes"""
        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": False,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.seal_file", return_value=0) as mock_seal:
                cmd_seal_file(args)

                captured = capsys.readouterr()
                assert "No values found to encrypt" in captured.out

    def test_cmd_seal_file_prefix_only_no_changes(self, temp_env_file, capsys):
        """Test seal-file prefix-only with no changes"""
        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": True,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.seal_file", return_value=0) as mock_seal:
                cmd_seal_file(args)

                captured = capsys.readouterr()
                assert (
                    "No values starting with EnvSeal prefix found to encrypt"
                    in captured.out
                )

    def test_cmd_unseal_file_success(self, temp_env_file, capsys):
        """Test successful unseal-file command"""
        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": False,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.unseal_file", return_value=2) as mock_unseal:
                cmd_unseal_file(args)

                mock_unseal.assert_called_once()
                captured = capsys.readouterr()
                assert "Successfully decrypted 2 value(s)" in captured.out

    def test_cmd_unseal_file_no_changes(self, temp_env_file, capsys):
        """Test unseal-file with no changes"""
        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": False,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.unseal_file", return_value=0) as mock_unseal:
                cmd_unseal_file(args)

                captured = capsys.readouterr()
                assert "No encrypted values found to decrypt" in captured.out

    def test_cmd_unseal_file_prefix_only_no_changes(self, temp_env_file, capsys):
        """Test unseal-file prefix-only with no changes"""
        args = type(
            "Args",
            (),
            {
                "file_path": Path(temp_env_file),
                "prefix_only": True,
                "output": None,
                "backup": False,
            },
        )()

        with patch("envseal.cli.get_passphrase_from_args", return_value=b"test"):
            with patch("envseal.cli.unseal_file", return_value=0) as mock_unseal:
                cmd_unseal_file(args)

                captured = capsys.readouterr()
                assert (
                    "No encrypted values with EnvSeal prefix found to decrypt"
                    in captured.out
                )
