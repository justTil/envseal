"""
Tests for CLI error handling
"""

import sys
import subprocess


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_wrong_passphrase_error(self):
        """Test CLI error handling with wrong passphrase"""
        # Create a token with one passphrase
        correct_passphrase = "correct-passphrase"
        wrong_passphrase = "wrong-passphrase"

        from envseal.core import seal

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

        assert result.returncode == 2  # argparse error code

    def test_file_not_found_error(self):
        """Test CLI error when file not found"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "envseal.cli",
                "seal-file",
                "/nonexistent/file.env",
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                "test",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Error:" in result.stderr
        assert "File not found" in result.stderr
