"""
Tests for envseal.cli
"""

import os
import sys
import tempfile
import subprocess
from unittest.mock import patch


from envseal.cli import main, create_parser, get_passphrase_from_args
from envseal.core import seal, TOKEN_PREFIX


class TestCLIParser:
    """Test CLI argument parsing"""

    def test_create_parser(self):
        """Test parser creation"""
        parser = create_parser()
        assert parser.prog == "envseal"

    def test_seal_command_args(self):
        """Test seal command argument parsing"""
        parser = create_parser()
        args = parser.parse_args(
            [
                "seal",
                "test-value",
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                "test-pass",
            ]
        )

        assert args.command == "seal"
        assert args.value == "test-value"
        assert args.passphrase_source == "hardcoded"
        assert args.hardcoded_passphrase == "test-pass"

    def test_unseal_command_args(self):
        """Test unseal command argument parsing"""
        parser = create_parser()
        args = parser.parse_args(
            [
                "unseal",
                "ENC[v1]:token",
                "--passphrase-source",
                "env_var",
                "--env-var",
                "MY_PASSPHRASE",
            ]
        )

        assert args.command == "unseal"
        assert args.token == "ENC[v1]:token"
        assert args.passphrase_source == "env_var"
        assert args.env_var == "MY_PASSPHRASE"


class TestGetPassphraseFromArgs:
    """Test passphrase extraction from CLI arguments"""

    def test_hardcoded_passphrase_args(self):
        """Test extracting hardcoded passphrase from args"""
        # Mock argparse.Namespace
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


class TestCLICommands:
    """Test CLI command execution"""

    def test_seal_command_execution(self):
        """Test seal command through main function"""
        test_args = [
            "seal",
            "test-secret",
            "--passphrase-source",
            "hardcoded",
            "--hardcoded-passphrase",
            "test-passphrase",
        ]

        with patch("sys.argv", ["envseal"] + test_args):
            with patch("builtins.print") as mock_print:
                main()

                # Check that something was printed (the encrypted token)
                mock_print.assert_called_once()
                printed_value = mock_print.call_args[0][0]
                assert printed_value.startswith(TOKEN_PREFIX)

    def test_unseal_command_execution(self):
        """Test unseal command through main function"""
        # First create an encrypted token
        passphrase = b"test-passphrase"
        plaintext = "test-secret"
        token = seal(plaintext, passphrase)

        test_args = [
            "unseal",
            token,
            "--passphrase-source",
            "hardcoded",
            "--hardcoded-passphrase",
            "test-passphrase",
        ]

        with patch("sys.argv", ["envseal"] + test_args):
            with patch("builtins.print") as mock_print:
                main()

                mock_print.assert_called_once_with(plaintext)

    @patch("envseal.cli.store_passphrase_in_keyring")
    def test_store_passphrase_command(self, mock_store):
        """Test store-passphrase command"""
        test_args = [
            "store-passphrase",
            "my-passphrase",
            "--app-name",
            "test-app",
            "--key-alias",
            "test-key",
        ]

        with patch("sys.argv", ["envseal"] + test_args):
            with patch("builtins.print") as mock_print:
                main()

                mock_store.assert_called_once_with(
                    "my-passphrase", app_name="test-app", key_alias="test-key"
                )
                mock_print.assert_called_once_with(
                    "Passphrase stored in keyring for test-app:test-key"
                )


class TestCLIIntegration:
    """Integration tests using subprocess"""

    def test_cli_seal_unseal_integration(self):
        """Test complete seal/unseal cycle via CLI"""
        passphrase = "integration-test-passphrase"
        secret_value = "super-secret-data"

        # Test seal command
        seal_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "envseal.cli",
                "seal",
                secret_value,
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                passphrase,
            ],
            capture_output=True,
            text=True,
        )

        assert seal_result.returncode == 0
        encrypted_token = seal_result.stdout.strip()
        assert encrypted_token.startswith(TOKEN_PREFIX)

        # Test unseal command
        unseal_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "envseal.cli",
                "unseal",
                encrypted_token,
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                passphrase,
            ],
            capture_output=True,
            text=True,
        )

        assert unseal_result.returncode == 0
        decrypted_value = unseal_result.stdout.strip()
        assert decrypted_value == secret_value

    def test_cli_load_env_command(self):
        """Test load-env command via CLI"""
        passphrase = "env-test-passphrase"
        secret_value = "secret-database-password"

        # Create encrypted token
        passphrase_bytes = passphrase.encode()
        encrypted_token = seal(secret_value, passphrase_bytes)

        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"PLAIN_VAR=plain-value\n")
            f.write(f"SECRET_VAR={encrypted_token}\n")
            env_path = f.name

        try:
            # Test load-env command
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "envseal.cli",
                    "load-env",
                    "--env-file",
                    env_path,
                    "--passphrase-source",
                    "hardcoded",
                    "--hardcoded-passphrase",
                    passphrase,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            output_lines = result.stdout.strip().split("\n")

            # Should contain both variables
            assert "PLAIN_VAR=plain-value" in output_lines
            assert "SECRET_VAR=secret-database-password" in output_lines

        finally:
            os.unlink(env_path)


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_wrong_passphrase_error(self):
        """Test CLI error handling with wrong passphrase"""
        # Create a token with one passphrase
        correct_passphrase = "correct-passphrase"
        wrong_passphrase = "wrong-passphrase"

        token = seal("test-data", correct_passphrase.encode())

        # Try to decrypt with wrong passphrase
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "envseal.cli",
                "unseal",
                token,
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                wrong_passphrase,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Error:" in result.stderr
        assert "Decryption failed" in result.stderr

    def test_missing_passphrase_error(self):
        """Test CLI error when passphrase is missing"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "envseal.cli",
                "seal",
                "test-value",
                "--passphrase-source",
                "env_var",
                "--env-var",
                "NONEXISTENT_VAR",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Error:" in result.stderr
        assert "not found" in result.stderr

    def test_invalid_command(self):
        """Test CLI with invalid command"""
        result = subprocess.run(
            [sys.executable, "-m", "envseal.cli", "invalid-command"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

    def test_no_command_shows_help(self):
        """Test that no command shows help"""
        result = subprocess.run(
            [sys.executable, "-m", "envseal.cli"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()
