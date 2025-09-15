"""
EnvSeal - Encrypt sensitive values in environment files using AES-GCM
"""

from .core import (
    seal,
    unseal,
    get_passphrase,
    store_passphrase_in_keyring,
    apply_sealed_env,
    EnvSealError,
    PassphraseSource,
    load_sealed_env,
)

__version__ = "0.1.0"
__all__ = [
    "seal",
    "unseal",
    "get_passphrase",
    "store_passphrase_in_keyring",
    "apply_sealed_env",
    "EnvSealError",
    "PassphraseSource",
    "load_sealed_env",
]
