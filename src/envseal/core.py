"""
Core functionality for EnvSeal - AES-GCM encryption for environment variables
"""

import os
import keyring
import json
import base64
import getpass
import re
from enum import Enum
from typing import Optional, Union, Dict, Any
from pathlib import Path

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from dotenv import load_dotenv, dotenv_values

try:
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

try:
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


APP_NAME = "envseal"
KEY_ALIAS = "master_v1"
TOKEN_PREFIX = "ENC[v1]:"


class EnvSealError(Exception):
    """Base exception for EnvSeal operations"""

    pass


class PassphraseSource(Enum):
    """Available sources for passphrases"""

    KEYRING = "keyring"
    HARDCODED = "hardcoded"
    ENV_VAR = "env_var"
    DOTENV = "dotenv"
    PROMPT = "prompt"


def _kdf(passphrase: bytes, salt: bytes) -> bytes:
    """Key derivation function using Scrypt"""
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(passphrase)


def get_passphrase(
    source: PassphraseSource = PassphraseSource.KEYRING,
    hardcoded_passphrase: Optional[str] = None,
    env_var_name: str = "ENVSEAL_PASSPHRASE",
    dotenv_path: Optional[Union[str, Path]] = None,
    dotenv_var_name: str = "ENVSEAL_PASSPHRASE",
    app_name: str = APP_NAME,
    key_alias: str = KEY_ALIAS,
    prompt_text: str = "EnvSeal master passphrase: ",
) -> bytes:
    """
    Get passphrase from various sources.

    Args:
        source: Where to get the passphrase from
        hardcoded_passphrase: Passphrase to use when source is HARDCODED
        env_var_name: Environment variable name for ENV_VAR source
        dotenv_path: Path to .env file for DOTENV source
        dotenv_var_name: Variable name in .env file for DOTENV source
        app_name: Application name for keyring
        key_alias: Key alias for keyring
        prompt_text: Text to show when prompting user

    Returns:
        bytes: The passphrase as bytes

    Raises:
        EnvSealError: If passphrase cannot be obtained from specified source
    """
    passphrase = None

    if source == PassphraseSource.KEYRING:
        if not HAS_KEYRING:
            raise EnvSealError(
                "keyring package not available. Install with: pip install keyring"
            )
        try:
            passphrase = keyring.get_password(app_name, key_alias)
            if not passphrase:
                raise EnvSealError(
                    f"No passphrase found in keyring for {app_name}:{key_alias}"
                )
        except Exception as e:
            raise EnvSealError(f"Failed to get passphrase from keyring: {e}")

    elif source == PassphraseSource.HARDCODED:
        if not hardcoded_passphrase:
            raise EnvSealError(
                "hardcoded_passphrase must be provided when using HARDCODED source"
            )
        passphrase = hardcoded_passphrase

    elif source == PassphraseSource.ENV_VAR:
        passphrase = os.environ.get(env_var_name)
        if not passphrase:
            raise EnvSealError(f"Environment variable {env_var_name} not found")

    elif source == PassphraseSource.DOTENV:
        if not HAS_DOTENV:
            raise EnvSealError(
                "python-dotenv package not available. Install with: pip install python-dotenv"
            )

        if dotenv_path:
            # Load from specific file
            env_vars = dotenv_values(dotenv_path)
            passphrase = env_vars.get(dotenv_var_name)
        else:
            # Load from default locations
            load_dotenv()
            passphrase = os.environ.get(dotenv_var_name)

        if not passphrase:
            raise EnvSealError(f"Variable {dotenv_var_name} not found in .env file")

    elif source == PassphraseSource.PROMPT:
        try:
            passphrase = getpass.getpass(prompt_text)
            if not passphrase:
                raise EnvSealError("Empty passphrase provided")
        except (KeyboardInterrupt, EOFError):
            raise EnvSealError("Passphrase input cancelled")

    else:
        raise EnvSealError(f"Unknown passphrase source: {source}")

    return passphrase.encode("utf-8")


def seal(plaintext: Union[str, bytes], passphrase: bytes) -> str:
    """
    Encrypt plaintext using AES-GCM.

    Args:
        plaintext: Text to encrypt
        passphrase: Encryption passphrase

    Returns:
        str: Encrypted token with format "ENC[v1]:..."
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")

    # Generate random salt and nonce
    salt = os.urandom(16)
    nonce = os.urandom(12)

    # Derive key and encrypt
    key = _kdf(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)

    # Create token structure
    blob = {
        "s": base64.b64encode(salt).decode(),
        "n": base64.b64encode(nonce).decode(),
        "c": base64.b64encode(ciphertext).decode(),
    }

    # Encode as base64 JSON
    token_data = base64.b64encode(json.dumps(blob).encode()).decode()
    return f"{TOKEN_PREFIX}{token_data}"


def unseal(token: str, passphrase: bytes) -> bytes:
    """
    Decrypt an encrypted token.

    Args:
        token: Encrypted token starting with "ENC[v1]:"
        passphrase: Decryption passphrase

    Returns:
        bytes: Decrypted plaintext

    Raises:
        EnvSealError: If token is malformed or decryption fails
    """
    if not token.startswith(TOKEN_PREFIX):
        raise EnvSealError(
            f"Invalid token format. Expected token to start with {TOKEN_PREFIX}"
        )

    try:
        # Extract and decode token data
        token_data = token[len(TOKEN_PREFIX) :]
        blob_json = base64.b64decode(token_data)
        blob = json.loads(blob_json)

        # Extract components
        salt = base64.b64decode(blob["s"])
        nonce = base64.b64decode(blob["n"])
        ciphertext = base64.b64decode(blob["c"])

    except (KeyError, json.JSONDecodeError, base64.binascii.Error) as e:
        raise EnvSealError(f"Malformed token: {e}")

    try:
        # Derive key and decrypt
        key = _kdf(passphrase, salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        return plaintext

    except InvalidTag:
        raise EnvSealError("Decryption failed. Wrong passphrase or corrupted token.")


def store_passphrase_in_keyring(
    passphrase: str, app_name: str = APP_NAME, key_alias: str = KEY_ALIAS
) -> None:
    """
    Store passphrase in OS keyring for future use.

    Args:
        passphrase: The passphrase to store
        app_name: Application name for keyring
        key_alias: Key alias for keyring

    Raises:
        EnvSealError: If keyring is not available or storage fails
    """
    if not HAS_KEYRING:
        raise EnvSealError(
            "keyring package not available. Install with: pip install keyring"
        )

    try:
        keyring.set_password(app_name, key_alias, passphrase)
    except Exception as e:
        raise EnvSealError(f"Failed to store passphrase in keyring: {e}")


def seal_file(
    file_path: Union[str, Path],
    passphrase: bytes,
    output_path: Optional[Union[str, Path]] = None,
    prefix_only: bool = False,
) -> int:
    """
    Encrypt values in an environment file (key=value format).

    Args:
        file_path: Path to the environment file to process
        passphrase: Encryption passphrase
        output_path: Output file path (if None, overwrites input file)
        prefix_only: If True, only encrypt values that start with TOKEN_PREFIX (treating it as a marker)

    Returns:
        int: Number of values that were encrypted/re-encrypted

    Raises:
        EnvSealError: If file operations or encryption fails
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise EnvSealError(f"File not found: {file_path}")

    if output_path is None:
        output_path = file_path
    else:
        output_path = Path(output_path)

    try:
        # Read the file
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        modified_count = 0
        processed_lines = []

        # Pattern to match key=value lines (allowing for whitespace)
        env_pattern = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")

        for line in lines:
            match = env_pattern.match(line)

            if match:
                indent, key, value = match.groups()

                # Remove quotes if present
                original_value = value
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                    quoted = True
                else:
                    quoted = False

                should_encrypt = False

                if prefix_only:
                    # Only encrypt if it starts with our prefix (treating prefix as a marker)
                    if value.startswith(TOKEN_PREFIX):
                        should_encrypt = True

                        # Check if it's already properly encrypted
                        try:
                            # Try to decrypt - if successful, it's already encrypted, so re-encrypt
                            decrypted = unseal(value, passphrase)
                            value = decrypted.decode("utf-8")
                        except EnvSealError:
                            # If decryption fails, treat everything after TOKEN_PREFIX as plaintext
                            # This handles cases like: port=ENC[v1]:5433 where 5433 is not encrypted
                            value = value[len(TOKEN_PREFIX) :]
                else:
                    # Encrypt all values except those already properly encrypted
                    if value.strip():
                        # Check if it's already properly encrypted
                        if value.startswith(TOKEN_PREFIX):
                            try:
                                # Try to decrypt - if successful, it's already encrypted
                                unseal(value, passphrase)
                                should_encrypt = False  # Already encrypted, skip
                            except EnvSealError:
                                # Not properly encrypted, so encrypt it
                                should_encrypt = True
                                value = value[len(TOKEN_PREFIX) :]
                        else:
                            # Not encrypted at all
                            should_encrypt = True

                if should_encrypt:
                    # Encrypt the value
                    encrypted_value = seal(value, passphrase)

                    # Preserve quoting if original was quoted
                    if quoted:
                        encrypted_value = f'"{encrypted_value}"'

                    processed_lines.append(f"{indent}{key}={encrypted_value}")
                    modified_count += 1
                else:
                    # Keep the line as-is
                    processed_lines.append(line)
            else:
                # Not a key=value line, keep as-is
                processed_lines.append(line)

        # Write the output
        output_content = "\n".join(processed_lines)
        if content.endswith("\n"):
            output_content += "\n"

        output_path.write_text(output_content, encoding="utf-8")

        return modified_count

    except Exception as e:
        if isinstance(e, EnvSealError):
            raise
        raise EnvSealError(f"Failed to process file {file_path}: {e}")


def load_sealed_env(
    dotenv_path: Optional[Union[str, Path]] = None,
    passphrase_source: PassphraseSource = PassphraseSource.KEYRING,
    **passphrase_kwargs: Any,
) -> Dict[str, str]:
    """
    Load environment variables from a .env file, automatically unsealing encrypted values.

    Args:
        dotenv_path: Path to .env file. If None, uses default dotenv behavior
        passphrase_source: Source for the decryption passphrase
        **passphrase_kwargs: Additional arguments passed to get_passphrase()

    Returns:
        dict: Environment variables with encrypted values decrypted

    Raises:
        EnvSealError: If dotenv is not available or decryption fails
    """
    if not HAS_DOTENV:
        raise EnvSealError(
            "python-dotenv package not available. Install with: pip install python-dotenv"
        )

    # Get passphrase
    passphrase = get_passphrase(source=passphrase_source, **passphrase_kwargs)

    # Load environment variables
    if dotenv_path:
        env_vars = dotenv_values(dotenv_path)
    else:
        # Load from default locations but don't modify os.environ
        env_vars = dotenv_values()

    # Decrypt sealed values
    result = {}
    for key, value in env_vars.items():
        if value and value.startswith(TOKEN_PREFIX):
            try:
                decrypted = unseal(value, passphrase)
                result[key] = decrypted.decode("utf-8")
            except EnvSealError as e:
                raise EnvSealError(f"Failed to unseal {key}: {e}")
        else:
            result[key] = value

    return result


def apply_sealed_env(
    dotenv_path: Optional[Union[str, Path]] = None,
    passphrase_source: PassphraseSource = PassphraseSource.KEYRING,
    override: bool = False,
    **passphrase_kwargs: Any,
) -> None:
    """
    Load sealed environment variables and apply them to os.environ.

    Args:
        dotenv_path: Path to .env file
        passphrase_source: Source for the decryption passphrase
        override: Whether to override existing environment variables
        **passphrase_kwargs: Additional arguments passed to get_passphrase()
    """
    env_vars = load_sealed_env(
        dotenv_path=dotenv_path,
        passphrase_source=passphrase_source,
        **passphrase_kwargs,
    )

    for key, value in env_vars.items():
        if key is not None and value is not None:
            if override or key not in os.environ:
                os.environ[key] = value
