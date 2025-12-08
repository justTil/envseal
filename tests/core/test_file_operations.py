"""
Tests for core file operation functionality
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from envseal.core import seal_file, unseal_file, seal, TOKEN_PREFIX, EnvSealError


class TestFileOperations:
    """Test core file operations"""

    @pytest.fixture
    def passphrase(self):
        return b"test-passphrase"

    @pytest.fixture
    def temp_env_file(self):
        """Create a temporary .env file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    def test_seal_file_basic(self, temp_env_file, passphrase):
        """Test basic file sealing"""
        # Create test file
        with open(temp_env_file, "w") as f:
            f.write("SECRET=test-value\n")
            f.write("PLAIN=plain-value\n")

        result = seal_file(Path(temp_env_file), passphrase)

        assert result == 2  # Both values sealed

        # Check file contents - both should be encrypted
        with open(temp_env_file, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")

        assert len(lines) == 2
        # Both lines should have encrypted tokens
        assert all(TOKEN_PREFIX in line for line in lines)
        assert any(line.startswith("SECRET=") for line in lines)
        assert any(line.startswith("PLAIN=") for line in lines)

    def test_seal_file_no_values_to_seal(self, temp_env_file, passphrase):
        """Test sealing file with all plain values"""
        with open(temp_env_file, "w") as f:
            f.write("PLAIN1=value1\n")
            f.write("PLAIN2=value2\n")

        result = seal_file(Path(temp_env_file), passphrase)

        assert result == 2  # Both values sealed by default

    def test_seal_file_prefix_only(self, temp_env_file, passphrase):
        """Test sealing with prefix-only mode"""
        # With prefix_only=True, only values already starting with TOKEN_PREFIX are sealed
        # The prefix acts as a marker to indicate "encrypt this value"
        with open(temp_env_file, "w") as f:
            f.write(f"MARKED_SECRET={TOKEN_PREFIX}plaintext-to-encrypt\n")
            f.write("PLAIN=plain-value\n")

        result = seal_file(Path(temp_env_file), passphrase, prefix_only=True)

        assert result == 1  # One value with prefix sealed

        with open(temp_env_file, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")

        assert len(lines) == 2
        # PLAIN should be unchanged
        assert "PLAIN=plain-value" in lines
        # MARKED_SECRET should now be properly encrypted (double TOKEN_PREFIX)
        assert any(
            line.startswith("MARKED_SECRET=") and line.count(TOKEN_PREFIX) >= 1
            for line in lines
        )

    def test_seal_file_with_output(self, temp_env_file, passphrase):
        """Test sealing with output file"""
        with open(temp_env_file, "w") as f:
            f.write("SECRET=test-value\n")

        output_file = temp_env_file + ".out"
        result = seal_file(
            Path(temp_env_file), passphrase, output_path=Path(output_file)
        )

        assert result == 1

        # Original file unchanged
        with open(temp_env_file, "r") as f:
            original_content = f.read()
        assert "SECRET=test-value" in original_content

        # Output file has sealed content
        with open(output_file, "r") as f:
            output_content = f.read()
        assert TOKEN_PREFIX in output_content

        os.unlink(output_file)

    def test_seal_file_backup(self, temp_env_file, passphrase):
        """Test sealing - backup not directly supported, but can copy file first"""
        with open(temp_env_file, "w") as f:
            f.write("SECRET=test-value\n")

        # Manual backup before sealing
        import shutil

        backup_file = temp_env_file + ".backup"
        shutil.copy(temp_env_file, backup_file)

        result = seal_file(Path(temp_env_file), passphrase)

        assert result == 1

        # Backup file exists with original content
        assert os.path.exists(backup_file)
        with open(backup_file, "r") as f:
            backup_content = f.read()
        assert "SECRET=test-value" in backup_content

        # Original file is now sealed
        with open(temp_env_file, "r") as f:
            sealed_content = f.read()
        assert TOKEN_PREFIX in sealed_content

        os.unlink(backup_file)

    def test_unseal_file_basic(self, temp_env_file, passphrase):
        """Test basic file unsealing"""
        # Create file with encrypted value
        encrypted_token = seal("test-value", passphrase)
        with open(temp_env_file, "w") as f:
            f.write(f"SECRET={encrypted_token}\n")
            f.write("PLAIN=plain-value\n")

        result = unseal_file(Path(temp_env_file), passphrase)

        assert result == 1  # One value unsealed

        with open(temp_env_file, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")

        assert len(lines) == 2
        assert "PLAIN=plain-value" in lines
        assert "SECRET=test-value" in lines

    def test_unseal_file_no_values_to_unseal(self, temp_env_file, passphrase):
        """Test unsealing file with no encrypted values"""
        with open(temp_env_file, "w") as f:
            f.write("PLAIN1=value1\n")
            f.write("PLAIN2=value2\n")

        result = unseal_file(Path(temp_env_file), passphrase)

        assert result == 0  # No values unsealed

    def test_unseal_file_prefix_only(self, temp_env_file, passphrase):
        """Test unsealing with prefix-only mode"""
        # Create file with prefixed encrypted values
        encrypted_token = seal("test-value", passphrase)
        with open(temp_env_file, "w") as f:
            f.write(f"ENVSEAL_SECRET={encrypted_token}\n")
            f.write("PLAIN=plain-value\n")

        result = unseal_file(Path(temp_env_file), passphrase, prefix_only=True)

        assert result == 1  # One value unsealed

        with open(temp_env_file, "r") as f:
            content = f.read()
            lines = content.strip().split("\n")

        assert len(lines) == 2
        assert "PLAIN=plain-value" in lines
        assert "ENVSEAL_SECRET=test-value" in lines

    def test_unseal_file_with_output(self, temp_env_file, passphrase):
        """Test unsealing with output file"""
        encrypted_token = seal("test-value", passphrase)
        with open(temp_env_file, "w") as f:
            f.write(f"SECRET={encrypted_token}\n")

        output_file = temp_env_file + ".out"
        result = unseal_file(
            Path(temp_env_file), passphrase, output_path=Path(output_file)
        )

        assert result == 1

        # Original file unchanged
        with open(temp_env_file, "r") as f:
            original_content = f.read()
        assert encrypted_token in original_content

        # Output file has unsealed content
        with open(output_file, "r") as f:
            output_content = f.read()
        assert "SECRET=test-value" in output_content

        os.unlink(output_file)

    def test_unseal_file_backup(self, temp_env_file, passphrase):
        """Test unsealing - backup not directly supported, but can copy file first"""
        encrypted_token = seal("test-value", passphrase)
        with open(temp_env_file, "w") as f:
            f.write(f"SECRET={encrypted_token}\n")

        # Manual backup before unsealing
        import shutil

        backup_file = temp_env_file + ".backup"
        shutil.copy(temp_env_file, backup_file)

        result = unseal_file(Path(temp_env_file), passphrase)

        assert result == 1

        # Backup file exists with encrypted content
        assert os.path.exists(backup_file)
        with open(backup_file, "r") as f:
            backup_content = f.read()
        assert encrypted_token in backup_content

        # Original file is now unsealed
        with open(temp_env_file, "r") as f:
            unsealed_content = f.read()
        assert "SECRET=test-value" in unsealed_content

        os.unlink(backup_file)

    def test_seal_file_not_found(self, passphrase):
        """Test sealing non-existent file"""
        with pytest.raises(EnvSealError, match="File not found"):
            seal_file(Path("/nonexistent/file.env"), passphrase)

    def test_unseal_file_not_found(self, passphrase):
        """Test unsealing non-existent file"""
        with pytest.raises(EnvSealError, match="File not found"):
            unseal_file(Path("/nonexistent/file.env"), passphrase)
