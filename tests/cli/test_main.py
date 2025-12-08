"""
Tests for CLI main function
"""

from unittest.mock import patch
import pytest

from envseal.cli import main


class TestMainFunction:
    """Test the main CLI entry point"""

    def test_main_no_command_shows_help(self, capsys):
        """Test that main with no command shows help"""
        with patch("sys.argv", ["envseal"]):
            main()

            captured = capsys.readouterr()
            assert (
                "usage:" in captured.out.lower() or "usage:" in captured.stderr.lower()
            )

    def test_main_invalid_command_exits(self):
        """Test main with invalid command"""
        with patch("sys.argv", ["envseal", "invalid-command"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 2  # argparse returns 2 for invalid command

    @pytest.mark.parametrize(
        "command",
        ["seal", "unseal", "store-passphrase", "seal-file", "unseal-file"],
    )
    def test_main_command_dispatch(self, command):
        """Test that main dispatches to correct command functions"""
        cmd_name = f"cmd_{command.replace('-', '_')}"
        with patch("sys.argv", ["envseal", command, "test"]):
            with patch(f"envseal.cli.{cmd_name}") as mock_cmd:
                # Commands may exit, so catch that
                try:
                    main()
                except SystemExit as e:
                    # Exit 0 is success
                    assert e.code == 0
                # Verify the command was called
                mock_cmd.assert_called_once()

    def test_main_load_env_dispatch(self):
        """Test that main dispatches to load-env command"""
        with patch("sys.argv", ["envseal", "load-env", "--env-file", "test.env"]):
            with patch("envseal.cli.cmd_load_env") as mock_cmd:
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
                mock_cmd.assert_called_once()
