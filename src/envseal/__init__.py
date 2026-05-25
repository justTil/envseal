"""
envseal - Encrypt sensitive values in environment files using AES-GCM
"""

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"
__author__ = "Til Schwarze"
__email__ = "tschwarze@envseal.org"

from .core import (
    seal,
    unseal,
    seal_file,
    unseal_file,
    get_passphrase,
    store_passphrase_in_keyring,
    apply_sealed_env,
    EnvSealError,
    PassphraseSource,
    load_sealed_env,
)

__all__ = [
    "seal",
    "unseal",
    "seal_file",
    "unseal_file",
    "get_passphrase",
    "store_passphrase_in_keyring",
    "apply_sealed_env",
    "EnvSealError",
    "PassphraseSource",
    "load_sealed_env",
]
