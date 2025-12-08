"""
Integration tests for CLI using subprocess
"""

import os
import sys
import tempfile
import subprocess

from envseal.core import seal, TOKEN_PREFIX


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

    def test_cli_load_env_integration(self):
        """Test load-env command via CLI"""
        passphrase = "env-test-passphrase"
        secret_value = "secret-database-password"

        # Create encrypted token
        passphrase_bytes = passphrase.encode()
        encrypted_token = seal(secret_value, passphrase_bytes)

        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("PLAIN_VAR=plain-value\n")
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

    def test_cli_apply_env_integration(self):
        """Test load-env --apply command via CLI"""
        passphrase = "apply-test-passphrase"
        secret_value = "applied-secret"

        # Create encrypted token
        encrypted_token = seal(secret_value, passphrase.encode())

        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"TEST_APPLY_VAR={encrypted_token}\n")
            f.write("TEST_PLAIN_APPLY=plain-applied\n")
            env_path = f.name

        # Clear any existing values
        test_vars = ["TEST_APPLY_VAR", "TEST_PLAIN_APPLY"]
        original_values = {}
        for var in test_vars:
            if var in os.environ:
                original_values[var] = os.environ[var]
                del os.environ[var]

        try:
            # Test load-env --apply command
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "envseal.cli",
                    "load-env",
                    "--env-file",
                    env_path,
                    "--apply",
                    "--passphrase-source",
                    "hardcoded",
                    "--hardcoded-passphrase",
                    passphrase,
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert "Environment variables loaded and applied" in result.stdout

            # Note: subprocess runs in separate process, so os.environ won't be affected
            # We can only verify the command succeeded via return code and output

        finally:
            # Cleanup
            for var in test_vars:
                if var in os.environ:
                    del os.environ[var]
                if var in original_values:
                    os.environ[var] = original_values[var]
            os.unlink(env_path)
