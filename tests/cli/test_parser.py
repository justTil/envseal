"""
Tests for CLI argument parsing functionality
"""

import pytest
from pathlib import Path

from envseal.cli import create_parser


class TestCLIParser:
    """Test CLI argument parsing"""

    def test_create_parser_basic(self):
        """Test parser creation"""
        parser = create_parser()
        assert parser.prog == "envseal"

        # Test that all commands are available
        help_text = parser.format_help()
        assert "seal" in help_text
        assert "unseal" in help_text
        assert "store-passphrase" in help_text
        assert "load-env" in help_text
        assert "seal-file" in help_text
        assert "unseal-file" in help_text

    @pytest.mark.parametrize(
        "command,expected_args",
        [
            ("seal", ["value"]),
            ("unseal", ["token"]),
            ("store-passphrase", ["passphrase"]),
            ("load-env", []),
            ("seal-file", ["file_path"]),
            ("unseal-file", ["file_path"]),
        ],
    )
    def test_command_parsing(self, command, expected_args):
        """Test parsing of individual commands"""
        parser = create_parser()

        # Test basic command parsing
        args = parser.parse_args([command] + ["test"] * len(expected_args))
        assert args.command == command

        # Test with passphrase args
        if command in ["seal", "unseal", "load-env", "seal-file", "unseal-file"]:
            args = parser.parse_args(
                [
                    command,
                    *["test"] * len(expected_args),
                    "--passphrase-source",
                    "hardcoded",
                    "--hardcoded-passphrase",
                    "test-pass",
                ]
            )
            assert args.passphrase_source == "hardcoded"
            assert args.hardcoded_passphrase == "test-pass"

    def test_load_env_specific_args(self):
        """Test load-env specific arguments"""
        parser = create_parser()
        args = parser.parse_args(
            [
                "load-env",
                "--env-file",
                "/tmp/test.env",
                "--apply",
                "--override",
                "--passphrase-source",
                "env_var",
                "--env-var",
                "MY_VAR",
            ]
        )

        assert args.command == "load-env"
        assert args.env_file == Path("/tmp/test.env")
        assert args.apply is True
        assert args.override is True
        assert args.passphrase_source == "env_var"
        assert args.env_var == "MY_VAR"

    def test_file_operation_args(self):
        """Test file operation specific arguments"""
        parser = create_parser()

        # Test seal-file args
        args = parser.parse_args(
            [
                "seal-file",
                "/tmp/test.env",
                "--prefix-only",
                "--output",
                "/tmp/output.env",
                "--backup",
                "--passphrase-source",
                "hardcoded",
                "--hardcoded-passphrase",
                "test",
            ]
        )

        assert args.command == "seal-file"
        assert args.file_path == Path("/tmp/test.env")
        assert args.prefix_only is True
        assert args.output == Path("/tmp/output.env")
        assert args.backup is True

        # Test unseal-file args
        args = parser.parse_args(
            [
                "unseal-file",
                "/tmp/test.env",
                "--prefix-only",
                "--output",
                "/tmp/output.env",
                "--backup",
            ]
        )

        assert args.command == "unseal-file"
        assert args.prefix_only is True
