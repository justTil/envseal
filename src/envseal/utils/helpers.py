"""
Helper utilities for EnvSeal
"""

import os
from typing import Dict, List, Optional, Union
from pathlib import Path

from ..core import TOKEN_PREFIX, unseal, get_passphrase, PassphraseSource, EnvsealError


def is_sealed_value(value: str) -> bool:
    """
    Check if a string is an encrypted EnvSeal token.

    Args:
        value: String to check

    Returns:
        bool: True if value is a sealed token
    """
    return isinstance(value, str) and value.startswith(TOKEN_PREFIX)


def find_sealed_values(data: Dict[str, str]) -> List[str]:
    """
    Find all sealed values in a dictionary.

    Args:
        data: Dictionary to search

    Returns:
        list: Keys that have sealed values
    """
    return [key for key, value in data.items() if is_sealed_value(value)]


def bulk_unseal(
    data: Dict[str, str], passphrase: bytes, skip_errors: bool = False
) -> Dict[str, str]:
    """
    Unseal multiple values in a dictionary.

    Args:
        data: Dictionary with potentially sealed values
        passphrase: Decryption passphrase
        skip_errors: If True, skip values that fail to unseal

    Returns:
        dict: Dictionary with sealed values unsealed

    Raises:
        EnvsealError: If unsealing fails and skip_errors is False
    """
    result = {}

    for key, value in data.items():
        if is_sealed_value(value):
            try:
                unsealed = unseal(value, passphrase)
                result[key] = unsealed.decode("utf-8")
            except EnvsealError as e:
                if skip_errors:
                    result[key] = value  # Keep original value
                else:
                    raise EnvsealError(f"Failed to unseal {key}: {e}")
        else:
            result[key] = value

    return result


def validate_env_file(path: Union[str, Path]) -> None:
    """
    Validate that an environment file exists and is readable.

    Args:
        path: Path to environment file

    Raises:
        EnvsealError: If file doesn't exist or isn't readable
    """
    env_path = Path(path)

    if not env_path.exists():
        raise EnvsealError(f"Environment file not found: {path}")

    if not env_path.is_file():
        raise EnvsealError(f"Path is not a file: {path}")

    try:
        with open(env_path, "r") as f:
            f.read(1)  # Try to read one character
    except PermissionError:
        raise EnvsealError(f"Permission denied reading file: {path}")
    except Exception as e:
        raise EnvsealError(f"Error reading file {path}: {e}")


def get_default_env_paths() -> List[Path]:
    """
    Get list of default .env file paths to search.

    Returns:
        list: Potential .env file paths in order of preference
    """
    current_dir = Path.cwd()
    return [
        current_dir / ".env",
        current_dir / ".env.local",
        current_dir / ".environment",
        Path.home() / ".env",
    ]


def find_env_file() -> Optional[Path]:
    """
    Find the first existing .env file in default locations.

    Returns:
        Path or None: Path to found .env file, or None if not found
    """
    for path in get_default_env_paths():
        if path.exists() and path.is_file():
            return path
    return None


def auto_unseal_environ(
    passphrase_source: PassphraseSource = PassphraseSource.KEYRING,
    prefix_filter: Optional[str] = None,
    **passphrase_kwargs,
) -> Dict[str, str]:
    """
    Automatically unseal any sealed values in os.environ.

    Args:
        passphrase_source: Source for decryption passphrase
        prefix_filter: Only process variables starting with this prefix
        **passphrase_kwargs: Additional arguments for get_passphrase

    Returns:
        dict: Dictionary of unsealed environment variables

    Note:
        This function does not modify os.environ, only returns unsealed values
    """
    passphrase = get_passphrase(source=passphrase_source, **passphrase_kwargs)

    env_vars = {}
    for key, value in os.environ.items():
        if prefix_filter and not key.startswith(prefix_filter):
            continue

        if is_sealed_value(value):
            try:
                unsealed = unseal(value, passphrase)
                env_vars[key] = unsealed.decode("utf-8")
            except EnvsealError:
                # Skip values that fail to unseal
                continue
        else:
            env_vars[key] = value

    return env_vars
