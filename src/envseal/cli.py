"""
Command-line interface for EnvSeal
"""

import sys
import argparse
from pathlib import Path


from .core import (
    seal,
    unseal,
    get_passphrase,
    store_passphrase_in_keyring,
    load_sealed_env,
    apply_sealed_env,
    seal_file,
    unseal_file,
    PassphraseSource,
    EnvsealError,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog="envseal",
        description="Encrypt sensitive values in environment files using AES-GCM",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Seal command
    seal_parser = subparsers.add_parser("seal", help="Encrypt a value")
    seal_parser.add_argument("value", help="Value to encrypt")
    add_passphrase_args(seal_parser)

    # Unseal command
    unseal_parser = subparsers.add_parser("unseal", help="Decrypt a value")
    unseal_parser.add_argument("token", help="Encrypted token to decrypt")
    add_passphrase_args(unseal_parser)

    # Store passphrase command
    store_parser = subparsers.add_parser(
        "store-passphrase", help="Store passphrase in OS keyring"
    )
    store_parser.add_argument("passphrase", help="Passphrase to store")
    store_parser.add_argument("--app-name", default="envseal", help="Application name")
    store_parser.add_argument("--key-alias", default="envseal_v1", help="Key alias")

    # Load env command
    load_parser = subparsers.add_parser(
        "load-env", help="Load and decrypt environment variables from .env file"
    )
    load_parser.add_argument("--env-file", type=Path, help="Path to .env file")
    load_parser.add_argument(
        "--apply", action="store_true", help="Apply variables to current environment"
    )
    load_parser.add_argument(
        "--override",
        action="store_true",
        help="Override existing environment variables",
    )
    add_passphrase_args(load_parser)

    # Seal file command
    seal_file_parser = subparsers.add_parser(
        "seal-file", help="Encrypt values in an environment file"
    )
    seal_file_parser.add_argument(
        "file_path", type=Path, help="Path to the environment file"
    )
    seal_file_parser.add_argument(
        "--prefix-only",
        action="store_true",
        help="Only encrypt values that already start with the EnvSeal prefix",
    )
    seal_file_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (default: overwrite input file)",
    )
    seal_file_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the original file before modifying",
    )
    add_passphrase_args(seal_file_parser)

    # Unseal file command
    unseal_file_parser = subparsers.add_parser(
        "unseal-file", help="Decrypt values in an environment file"
    )
    unseal_file_parser.add_argument(
        "file_path", type=Path, help="Path to the environment file"
    )
    unseal_file_parser.add_argument(
        "--prefix-only",
        action="store_true",
        help="Only decrypt values that start with the EnvSeal prefix",
    )
    unseal_file_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (default: overwrite input file)",
    )
    unseal_file_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the original file before modifying",
    )
    add_passphrase_args(unseal_file_parser)

    return parser


def add_passphrase_args(parser: argparse.ArgumentParser) -> None:
    """Add passphrase-related arguments to a parser"""
    group = parser.add_argument_group("passphrase options")
    group.add_argument(
        "--passphrase-source",
        choices=[s.value for s in PassphraseSource],
        default=PassphraseSource.KEYRING.value,
        help="Source for the encryption passphrase",
    )
    group.add_argument(
        "--hardcoded-passphrase",
        help="Hardcoded passphrase (use with --passphrase-source=hardcoded)",
    )
    group.add_argument(
        "--env-var",
        default="ENVSEAL_PASSPHRASE",
        help="Environment variable name for passphrase (default: ENVSEAL_PASSPHRASE)",
    )
    group.add_argument(
        "--dotenv-file", type=Path, help="Path to .env file containing passphrase"
    )
    group.add_argument(
        "--dotenv-var",
        default="ENVSEAL_PASSPHRASE",
        help="Variable name in .env file for passphrase (default: ENVSEAL_PASSPHRASE)",
    )


def get_passphrase_from_args(args: argparse.Namespace) -> bytes:
    """Get passphrase based on CLI arguments"""
    source = PassphraseSource(args.passphrase_source)

    kwargs = {}
    if hasattr(args, "hardcoded_passphrase") and args.hardcoded_passphrase:
        kwargs["hardcoded_passphrase"] = args.hardcoded_passphrase
    if hasattr(args, "env_var"):
        kwargs["env_var_name"] = args.env_var
    if hasattr(args, "dotenv_file") and args.dotenv_file:
        kwargs["dotenv_path"] = args.dotenv_file
    if hasattr(args, "dotenv_var"):
        kwargs["dotenv_var_name"] = args.dotenv_var

    return get_passphrase(source=source, **kwargs)


def cmd_seal(args: argparse.Namespace) -> None:
    """Handle seal command"""
    try:
        passphrase = get_passphrase_from_args(args)
        token = seal(args.value, passphrase)
        print(token)
    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unseal(args: argparse.Namespace) -> None:
    """Handle unseal command"""
    try:
        passphrase = get_passphrase_from_args(args)
        plaintext = unseal(args.token, passphrase)
        print(plaintext.decode("utf-8"))
    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_store_passphrase(args: argparse.Namespace) -> None:
    """Handle store-passphrase command"""
    try:
        store_passphrase_in_keyring(
            args.passphrase, app_name=args.app_name, key_alias=args.key_alias
        )
        print(f"Passphrase stored in keyring for {args.app_name}:{args.key_alias}")
    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_load_env(args: argparse.Namespace) -> None:
    """Handle load-env command"""
    try:
        source = PassphraseSource(args.passphrase_source)
        passphrase_kwargs = {}

        if args.hardcoded_passphrase:
            passphrase_kwargs["hardcoded_passphrase"] = args.hardcoded_passphrase
        if args.env_var:
            passphrase_kwargs["env_var_name"] = args.env_var
        if args.dotenv_file:
            passphrase_kwargs["dotenv_path"] = args.dotenv_file
        if args.dotenv_var:
            passphrase_kwargs["dotenv_var_name"] = args.dotenv_var

        if args.apply:
            apply_sealed_env(
                dotenv_path=args.env_file,
                passphrase_source=source,
                override=args.override,
                **passphrase_kwargs,
            )
            print("Environment variables loaded and applied")
        else:
            env_vars = load_sealed_env(
                dotenv_path=args.env_file, passphrase_source=source, **passphrase_kwargs
            )

            for key, value in env_vars.items():
                if key and value is not None:
                    print(f"{key}={value}")

    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_seal_file(args: argparse.Namespace) -> None:
    """Handle seal-file command"""
    try:
        passphrase = get_passphrase_from_args(args)

        # Determine output path
        output_path = args.output if args.output else args.file_path

        # Create backup if requested
        if args.backup and output_path == args.file_path:
            backup_path = Path(f"{args.file_path}.backup")
            backup_path.write_text(args.file_path.read_text())
            print(f"Backup created: {backup_path}")

        # Seal the file
        modified_count = seal_file(
            file_path=args.file_path,
            passphrase=passphrase,
            output_path=output_path,
            prefix_only=args.prefix_only,
        )

        if modified_count == 0:
            if args.prefix_only:
                print("No values starting with EnvSeal prefix found to encrypt.")
            else:
                print("No values found to encrypt.")
        else:
            action = "re-encrypted" if args.prefix_only else "encrypted"
            print(f"Successfully {action} {modified_count} value(s) in {output_path}")

    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unseal_file(args: argparse.Namespace) -> None:
    """Handle unseal-file command"""
    try:
        passphrase = get_passphrase_from_args(args)

        # Determine output path
        output_path = args.output if args.output else args.file_path

        # Create backup if requested
        if args.backup and output_path == args.file_path:
            backup_path = Path(f"{args.file_path}.backup")
            backup_path.write_text(args.file_path.read_text())
            print(f"Backup created: {backup_path}")

        # Unseal the file
        modified_count = unseal_file(
            file_path=args.file_path,
            passphrase=passphrase,
            output_path=output_path,
            prefix_only=args.prefix_only,
        )

        if modified_count == 0:
            if args.prefix_only:
                print("No encrypted values with EnvSeal prefix found to decrypt.")
            else:
                print("No encrypted values found to decrypt.")
        else:
            print(f"Successfully decrypted {modified_count} value(s) in {output_path}")

    except EnvsealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "seal":
        cmd_seal(args)
    elif args.command == "unseal":
        cmd_unseal(args)
    elif args.command == "store-passphrase":
        cmd_store_passphrase(args)
    elif args.command == "load-env":
        cmd_load_env(args)
    elif args.command == "seal-file":
        cmd_seal_file(args)
    elif args.command == "unseal-file":
        cmd_unseal_file(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
