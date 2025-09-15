# EnvSeal Documentation

Welcome to EnvSeal - a Python package for encrypting sensitive values in environment files using AES-GCM encryption.

## Overview

EnvSeal allows you to:
- Encrypt sensitive values in your `.env` files
- Store encrypted values safely in version control
- Decrypt values at runtime using various passphrase sources
- Integrate seamlessly with python-dotenv

## Quick Start

### Installation

```bash
pip install envseal
```

### Basic Usage

1. **Encrypt a secret**:
   ```bash
   envseal store-passphrase "your-master-passphrase"
   envseal seal "my-secret-database-password"
   ```

2. **Add to .env file**:
   ```env
   DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ...
   ```

3. **Use in Python**:
   ```python
   from envseal import load_sealed_env, PassphraseSource
   
   env_vars = load_sealed_env(
       dotenv_path=".env",
       passphrase_source=PassphraseSource.KEYRING
   )
   
   db_password = env_vars["DB_PASSWORD"]  # Automatically decrypted
   ```

## Features

- **Strong Encryption**: Uses AES-GCM with Scrypt key derivation
- **Flexible Passphrase Management**: OS keyring, environment variables, .env files, hardcoded, or prompt
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Python Integration**: Easy integration with existing Python applications
- **CLI Tool**: Command-line interface for encryption/decryption operations

## Security Model

EnvSeal uses a simple but effective security model:

1. **Encryption**: Values are encrypted using AES-GCM with a 256-bit key
2. **Key Derivation**: Keys are derived from your master passphrase using Scrypt
3. **Salt & Nonce**: Each encrypted value uses a unique salt and nonce
4. **Token Format**: Encrypted values are stored as `ENC[v1]:base64-encoded-data`

The master passphrase is never stored alongside the encrypted data, ensuring that even if your `.env` file is compromised, the secrets remain protected.

## Passphrase Sources

EnvSeal supports multiple ways to provide the decryption passphrase:

### 1. OS Keyring (Recommended)
Store the passphrase securely in your OS keyring:
```bash
envseal store-passphrase "your-master-passphrase"
```

### 2. Environment Variables
```bash
export ENVSEAL_PASSPHRASE="your-master-passphrase"
```

### 3. .env Files
Create a separate `.env` file for the passphrase:
```env
ENVSEAL_PASSPHRASE=your-master-passphrase
```

### 4. Hardcoded (Development Only)
```python
passphrase = get_passphrase(
    PassphraseSource.HARDCODED,
    hardcoded_passphrase="dev-passphrase"
)
```

### 5. Interactive Prompt
```python
passphrase = get_passphrase(PassphraseSource.PROMPT)
```

## Best Practices

1. **Use OS Keyring in Production**: Store your master passphrase in the OS keyring for maximum security
2. **Separate Passphrase Storage**: Never store the passphrase in the same file as encrypted values
3. **Environment-Specific Keys**: Use different passphrases for different environments (dev, staging, prod)
4. **Regular Rotation**: Rotate your master passphrase periodically
5. **Access Control**: Limit access to systems that can decrypt your values
6. **Version Control**: It's safe to commit encrypted values to version control, but never commit the passphrase

## API Reference

See the [README.md](../README.md) for detailed API documentation.

## Examples

### Django Integration

```python
# settings.py
import os
from envseal import apply_sealed_env, PassphraseSource

# Load and apply sealed environment variables
apply_sealed_env(
    dotenv_path=".env",
    passphrase_source=PassphraseSource.KEYRING
)

# Use normally
DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
```

### FastAPI Integration

```python
# config.py
from pydantic import BaseSettings
from envseal import load_sealed_env, PassphraseSource

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    
    class Config:
        # Custom env loader that handles sealed values
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                lambda: load_sealed_env(
                    passphrase_source=PassphraseSource.KEYRING
                ),
                file_secret_settings,
            )

settings = Settings()
```

### CI/CD Integration

For CI/CD pipelines, you can inject the passphrase as a secret environment variable:

```yaml
# GitHub Actions example
- name: Run tests
  env:
    ENVSEAL_PASSPHRASE: ${{ secrets.ENVSEAL_PASSPHRASE }}
  run: |
    python -m pytest
```

Then in your application:
```python
from envseal import apply_sealed_env, PassphraseSource

apply_sealed_env(
    passphrase_source=PassphraseSource.ENV_VAR,
    env_var_name="ENVSEAL_PASSPHRASE"
)
```

## Troubleshooting

### Common Issues

1. **"Decryption failed" Error**
   - Check that you're using the correct passphrase
   - Verify the encrypted token hasn't been corrupted

2. **"keyring package not available" Error**
   - Install keyring: `pip install keyring`
   - Or use a different passphrase source

3. **"python-dotenv package not available" Error**
   - Install python-dotenv: `pip install python-dotenv`
   - Or load environment variables manually

### Debug Mode

You can enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from envseal import load_sealed_env
# ... your code
```

## Contributing

We welcome contributions! Please see the main repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.