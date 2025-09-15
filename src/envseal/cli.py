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
    PassphraseSource,
    EnvSealError,
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
    store_parser.add_argument("--key-alias", default="master_v1", help="Key alias")

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
    except EnvSealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unseal(args: argparse.Namespace) -> None:
    """Handle unseal command"""
    try:
        passphrase = get_passphrase_from_args(args)
        plaintext = unseal(args.token, passphrase)
        print(plaintext.decode("utf-8"))
    except EnvSealError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_store_passphrase(args: argparse.Namespace) -> None:
    """Handle store-passphrase command"""
    try:
        store_passphrase_in_keyring(
            args.passphrase, app_name=args.app_name, key_alias=args.key_alias
        )
        print(f"Passphrase stored in keyring for {args.app_name}:{args.key_alias}")
    except EnvSealError as e:
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

    except EnvSealError as e:
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
