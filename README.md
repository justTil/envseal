# EnvSeal

**Encrypt sensitive values in environment files using AES-GCM**

EnvSeal allows you to store encrypted values in your environment files (like `.env`) instead of plain-text secrets. It uses industry-standard AES-GCM encryption and provides flexible options for managing your master passphrase.

## Features

- 🔒 **Strong Encryption**: AES-GCM with Scrypt key derivation
- 🔑 **Flexible Passphrase Sources**: OS keyring, environment variables, .env files, hardcoded, or interactive prompt
- 🐍 **Easy Python Integration**: Works seamlessly with python-dotenv
- 💻 **Cross-Platform**: Works on Windows, macOS, and Linux
- 🛠️ **CLI & Library**: Use from command line or import as a Python library
- 📁 **No External Dependencies**: Only requires cryptography and optional keyring/python-dotenv

## Installation

```bash
pip install envseal
```

Optional dependencies:
```bash
# For OS keyring support
pip install envseal[keyring]

# For .env file support  
pip install envseal[dotenv]

# For development
pip install envseal[dev]
```

## Quick Start

### 1. Encrypt a value

```bash
# Using CLI with keyring (most secure)
envseal store-passphrase "my-super-secret-passphrase"
envseal seal "my-database-password"
# Output: ENC[v1]:eyJzIjoiNnZ...

# Or with environment variable
export ENVSEAL_PASSPHRASE="my-super-secret-passphrase"
envseal seal "my-database-password" --passphrase-source=env_var
```

### 2. Add to your .env file

```env
DATABASE_URL=postgresql://user:password@localhost/db
DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ...
API_KEY=ENC[v1]:eyJzIjoiOXR...
```

### 3. Use in your Python application

```python
import os
from envseal import load_sealed_env, PassphraseSource

# Load and decrypt all environment variables
env_vars = load_sealed_env(
    dotenv_path=".env",
    passphrase_source=PassphraseSource.KEYRING
)

# Access decrypted values
db_password = env_vars["DB_PASSWORD"]
api_key = env_vars["API_KEY"]

# Or apply directly to os.environ
from envseal import apply_sealed_env
apply_sealed_env(".env", PassphraseSource.KEYRING)
db_password = os.environ["DB_PASSWORD"]
```

## Usage Examples

### CLI Usage

#### Encrypt values
```bash
# Store passphrase in keyring (recommended)
envseal store-passphrase "your-master-passphrase"

# Encrypt a value using keyring passphrase
envseal seal "sensitive-data"

# Encrypt using environment variable
export ENVSEAL_PASSPHRASE="your-master-passphrase"
envseal seal "sensitive-data" --passphrase-source=env_var

# Encrypt using .env file
echo "ENVSEAL_PASSPHRASE=your-master-passphrase" > .passphrase.env
envseal seal "sensitive-data" --passphrase-source=dotenv --dotenv-file=.passphrase.env
```

#### Decrypt values
```bash
# Decrypt using keyring
envseal unseal "ENC[v1]:eyJzIjoiNnZ..."

# Decrypt using other sources
envseal unseal "ENC[v1]:eyJzIjoiNnZ..." --passphrase-source=env_var
```

#### Load environment files
```bash
# Load and display decrypted .env file
envseal load-env --env-file=.env

# Apply to current environment
envseal load-env --env-file=.env --apply
```

### Python Library Usage

#### Basic encryption/decryption
```python
from envseal import seal, unseal, get_passphrase, PassphraseSource

# Get passphrase from keyring
passphrase = get_passphrase(PassphraseSource.KEYRING)

# Encrypt
token = seal("my-secret-value", passphrase)
print(token)  # ENC[v1]:eyJzIjoiNnZ...

# Decrypt
plaintext = unseal(token, passphrase)
print(plaintext.decode())  # my-secret-value
```

#### Working with .env files
```python
from envseal import load_sealed_env, PassphraseSource

# Load with automatic decryption
env_vars = load_sealed_env(
    dotenv_path=".env",
    passphrase_source=PassphraseSource.KEYRING
)

# Access values
db_password = env_vars.get("DB_PASSWORD")
api_key = env_vars.get("API_KEY")
```

#### Different passphrase sources
```python
from envseal import get_passphrase, PassphraseSource

# From OS keyring
passphrase = get_passphrase(PassphraseSource.KEYRING)

# From environment variable
passphrase = get_passphrase(
    PassphraseSource.ENV_VAR,
    env_var_name="MY_PASSPHRASE"
)

# From .env file
passphrase = get_passphrase(
    PassphraseSource.DOTENV,
    dotenv_path=".secrets.env",
    dotenv_var_name="MASTER_KEY"
)

# Hardcoded (not recommended for production)
passphrase = get_passphrase(
    PassphraseSource.HARDCODED,
    hardcoded_passphrase="my-passphrase"
)

# Interactive prompt
passphrase = get_passphrase(PassphraseSource.PROMPT)
```

#### Integration with python-dotenv
```python
import os
from dotenv import load_dotenv
from envseal import unseal, get_passphrase, PassphraseSource

# Load .env file normally
load_dotenv()

# Get passphrase
passphrase = get_passphrase(PassphraseSource.KEYRING)

# Decrypt specific values
raw_password = os.environ["DB_PASSWORD"]
if raw_password.startswith("ENC[v1]:"):
    db_password = unseal(raw_password, passphrase).decode()
else:
    db_password = raw_password
```

## Passphrase Management

EnvSeal supports multiple ways to provide the master passphrase:

### 1. OS Keyring (Recommended)
```python
from envseal import store_passphrase_in_keyring

# Store once
store_passphrase_in_keyring("your-master-passphrase")

# Use automatically
passphrase = get_passphrase(PassphraseSource.KEYRING)
```

### 2. Environment Variables
```bash
export ENVSEAL_PASSPHRASE="your-master-passphrase"
```

```python
passphrase = get_passphrase(PassphraseSource.ENV_VAR)
```

### 3. .env Files
Create a separate `.env` file for the passphrase:
```env
# .passphrase.env
ENVSEAL_PASSPHRASE=your-master-passphrase
```

```python
passphrase = get_passphrase(
    PassphraseSource.DOTENV,
    dotenv_path=".passphrase.env"
)
```

### 4. Hardcoded (Development Only)
```python
passphrase = get_passphrase(
    PassphraseSource.HARDCODED,
    hardcoded_passphrase="dev-passphrase"
)
```

## Security Best Practices

1. **Use OS Keyring**: Store your master passphrase in the OS keyring for maximum security
2. **Separate Passphrase Storage**: Never store the passphrase in the same file as encrypted values
3. **Environment-Specific Keys**: Use different passphrases for different environments
4. **Regular Rotation**: Rotate your master passphrase periodically
5. **Access Control**: Limit access to systems that can decrypt your values

## API Reference

### Core Functions

#### `seal(plaintext, passphrase) -> str`
Encrypt plaintext using AES-GCM.

#### `unseal(token, passphrase) -> bytes`
Decrypt an encrypted token.

#### `get_passphrase(source, **kwargs) -> bytes`
Get passphrase from various sources.

#### `load_sealed_env(dotenv_path, passphrase_source, **kwargs) -> dict`
Load environment variables with automatic decryption.

#### `apply_sealed_env(dotenv_path, passphrase_source, override=False, **kwargs)`
Load and apply environment variables to `os.environ`.

### PassphraseSource Enum
- `KEYRING`: OS keyring
- `ENV_VAR`: Environment variable
- `DOTENV`: .env file
- `HARDCODED`: Hardcoded string
- `PROMPT`: Interactive prompt

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/envseal.git
cd envseal

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Changelog

### 0.1.0
- Initial release
- AES-GCM encryption
- Multiple passphrase sources
- CLI and library interfaces
- python-dotenv integration