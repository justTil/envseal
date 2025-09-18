<div align="center">
<img src="https://raw.githubusercontent.com/justtil/envseal/main/docs/header.png" alt="Logo and banner for the envseal python package" width="200">
</div>

# Envseal

**Encrypt sensitive values in environment files using AES-GCM**

EnvSeal allows you to store encrypted values in your environment files (like `.env`) instead of plain-text secrets. It uses industry-standard AES-GCM encryption and provides flexible options for managing your master passphrase.

## Installation
```bash
pip  install  envseal
```



## Features

- Strong Encryption: AES-GCM with Scrypt key derivation
    
-  Flexible Passphrase Sources: OS keyring, environment variables, .env files, hardcoded, or interactive prompt
    
- Easy Python Integration: Works seamlessly with python-dotenv
    
-  Cross-Platform: Works on Windows, macOS, and Linux
    
-  CLI & Library: Use from command line or import as a Python library
    
-  Bulk File Processing: Encrypt all values in a file or only specific marked values

## Quick Start

### Encrypt a value using CLI with keyring (most secure)
​With your virtual environment (venv or conda) activated, store your passphrase in the system keyring.  

> [!INFO]
> Use a unique application name (`APP_NAME`) and key alias (`KEY_ALIAS`) for different projects.    
> 
> Reusing the same values is acceptable during development, but for production it’s best to choose distinct names to avoid sharing the same passphrase across projects.

Standard Command:
```bash
envseal store-passphrase "your-passphrase" --app-name "my-app" --key-alias "my-key"
```
This will save the passphrase in your keyring.
> [!INFO]
> When using custom APP_NAME and KEY_ALIAS variables, you must specify the `APP_NAME` and `KEY_ALIAS` used for decryption later in your app. If you don’t, **envseal** falls back to its default keyring (if available). This key would be unable to decrypt your properties.
> 
On development servers, or if you prefer not to manage keyring entries, you may skip custom names and rely on the following default values:

Default values:    
- APP_NAME: envseal
- KEY_ALIAS: envseal_v1

**Save passphrase to keyring without specifying an app name or key alias:**
```bash
envseal store-passphrase "your-passphrase"
```

#### Seal/Encrypt your first secret
Now you can use the following command to seal (encrypt) your secret:
```bash
envseal  seal  "my-database-password"
```

​

# Output: ENC[v1]:eyJzIjoiNnZ...

​

​

# Or with environment variable

​

export ENVSEAL_PASSPHRASE="my-super-secret-passphrase"

​

envseal  seal  "my-database-password"  --passphrase-source=env_var

​

### 2. Encrypt an entire file

Note: This encrypts individual values within key-value pairs, not the file as a whole.

envseal seal-file .env

**Before encryption:**

DB_PASS=mypassword

API_TOKEN=mysecrettoken

**After encryption:**

DB_PASS=ENC[v1]:eyJzIjogIjVaZ0I3L3A0L05y...

API_TOKEN=ENC[v1]:eyJzIjogIm1IL1haTjd3VW...

#### **Advanced Options**

**Selective encryption (prefix-only mode)** Only encrypt values that are already marked with the `ENC[v1]:` prefix:

envseal seal-file .env --prefix-only

**Create backup before modifying** Automatically create a backup copy of the original file:

envseal seal-file .env --backup

**Output to different file** Save the encrypted version to a new file instead of modifying the original:

envseal seal-file .env --output .env.sealed

### 3. Decrypt an entire file

envseal unseal-file .env

**Before decryption:**

DB_PASS=ENC[v1]:eyJzIjogIjVaZ0I3L3A0L05y...

API_TOKEN=ENC[v1]:eyJzIjogIm1IL1haTjd3VW...

**After decryption:**

DB_PASS=mypassword

API_TOKEN=mysecrettoken

#### **Advanced Options**

**Only decrypt values that start with ENC[v1]: prefix**

envseal unseal-file .env --prefix-only

**Create a backup before modifying**

envseal unseal-file .env --backup

**Output to a different file**

envseal unseal-file .env --output .env.decrypted

### 4. Add to your .env file

DATABASE_URL=postgresql://user:password@localhost/db

DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ...

API_KEY=ENC[v1]:eyJzIjoiOXR...

### 5. Use in your Python application

​

import os

​

from envseal import load_sealed_env, PassphraseSource

​

​

# Load and decrypt all environment variables

​

env_vars = load_sealed_env(

    dotenv_path=".env", passphrase_source=PassphraseSource.KEYRING

)

​

​

# Access decrypted values

​

db_password = env_vars["DB_PASSWORD"]

​

api_key = env_vars["API_KEY"]

​

**Or apply directly to os.environ**

from envseal import apply_sealed_env

​

apply_sealed_env(".env", PassphraseSource.KEYRING)

​

db_password = os.environ["DB_PASSWORD"]

## Usage Examples

### CLI Usage

#### Load environment files

​

# Load and display decrypted .env file

​

envseal load-env --env-file=.env

​

​

# Apply to current environment

​

envseal load-env --env-file=.env --apply

​

### Python Library Usage

#### Basic encryption/decryption

from envseal import seal, unseal, get_passphrase, PassphraseSource

​

​

# Get passphrase from keyring (or a different provider)

passphrase: bytes = get_passphrase(PassphraseSource.KEYRING)

​

​

# Encrypt

token: str = seal("my-secret-value", passphrase)

print(token)  # f.e. ENC[v1]:eyJzIjoiNnZ...

​

​

# Decrypt

plaintext: bytes = unseal(token, passphrase)

print(plaintext.decode())  # my-secret-value

​

#### File encryption

from envseal import seal_file, get_passphrase, PassphraseSource

​

​

# Get passphrase

passphrase = get_passphrase(PassphraseSource.KEYRING)

​

​

# Encrypt all values in a file

modified_count = seal_file(

    file_path=".env",

    passphrase=passphrase,

    prefix_only=False,  # Encrypt all values

)

print(f"Encrypted {modified_count} values")

​

​

# Only encrypt values marked with ENC[v1]: prefix

modified_count = seal_file(

    file_path=".env",

    passphrase=passphrase,

    prefix_only=True,  # Only encrypt marked values

)

print(f"Encrypted {modified_count} marked values")

​

​

# Output to different file

seal_file(file_path=".env", passphrase=passphrase, output_path=".env.sealed")

#### Working with .env files

​

from envseal import load_sealed_env, PassphraseSource

​

​

# Load with automatic decryption

​

env_vars = load_sealed_env(

​

dotenv_path=".env",

​

passphrase_source=PassphraseSource.KEYRING

​

)

​

​

# Access values

​

db_password = env_vars.get("DB_PASSWORD")

​

api_key = env_vars.get("API_KEY")

​

#### Different passphrase sources

​

from envseal import get_passphrase, PassphraseSource

​

​

# From OS keyring

​

passphrase = get_passphrase(PassphraseSource.KEYRING)

​

​

# From environment variable

​

passphrase = get_passphrase(

​

PassphraseSource.ENV_VAR,

​

env_var_name="MY_PASSPHRASE"

​

)

​

​

# From .env file

​

passphrase = get_passphrase(

​

PassphraseSource.DOTENV,

​

dotenv_path=".secrets.env",

​

dotenv_var_name="MASTER_KEY"

​

)

​

​

# Hardcoded (not recommended for production)

​

passphrase = get_passphrase(

​

PassphraseSource.HARDCODED,

​

hardcoded_passphrase="my-passphrase"

​

)

​

​

# Interactive prompt

​

passphrase = get_passphrase(PassphraseSource.PROMPT)

​

#### Integration with python-dotenv

​

import os

​

from dotenv import load_dotenv

​

from envseal import unseal, get_passphrase, PassphraseSource

​

​

# Load .env file normally

​

load_dotenv()

​

​

# Get passphrase

​

passphrase = get_passphrase(PassphraseSource.KEYRING)

​

​

# Decrypt specific values

​

raw_password = os.environ["DB_PASSWORD"]

​

if raw_password.startswith("ENC[v1]:"):

​

db_password = unseal(raw_password, passphrase).decode()

​

else:

​

db_password = raw_password

​

## File Processing

The `seal-file` command processes environment files in key=value format and provides two modes:

### Standard Mode (Default)

Encrypts all unencrypted values in the file:

​

# Before

​

DATABASE_URL=postgresql://user:secret@localhost/db

​

API_KEY=abc123

​

ALREADY_SEALED=ENC[v1]:eyJzIjoiNnZ...

​

​

# After running: envseal seal-file .env

​

DATABASE_URL=ENC[v1]:eyJzIjoiOXR...

​

API_KEY=ENC[v1]:eyJzIjoiNnZ...

​

ALREADY_SEALED=ENC[v1]:eyJzIjoiNnZ... # Unchanged (already encrypted)

​

### Prefix-Only Mode (Selective Encryption)

Only encrypts values that are marked with the `ENC[v1]:` prefix. This allows you to manually control which values should be encrypted:

​

# Before - manually mark values you want encrypted

​

DATABASE_URL=postgresql://user:secret@localhost/db

​

API_KEY=abc123

​

DB_PASSWORD=ENC[v1]:my-secret-password

​

PORT=ENC[v1]:5432

​

​

# After running: envseal seal-file .env --prefix-only

​

DATABASE_URL=postgresql://user:secret@localhost/db  # Unchanged (no prefix)

​

API_KEY=abc123  # Unchanged (no prefix)

​

DB_PASSWORD=ENC[v1]:eyJzIjoiOXR... # Encrypted (had prefix marker)

​

PORT=ENC[v1]:eyJzIjoiNnZ... # Encrypted (had prefix marker)

​

**Workflow for selective encryption:**

1. Edit your .env file and add `ENC[v1]:` prefix to values you want encrypted:
    

​

# Public/non-sensitive values - no prefix

​

APP_NAME=myapp

​

LOG_LEVEL=info

​

# Sensitive values - add ENC[v1]: prefix as marker

​

DB_PASSWORD=ENC[v1]:my-secret-password

​

API_KEY=ENC[v1]:sk-1234567890abcdef

​

2. Run `envseal seal-file .env --prefix-only` to encrypt only the marked values
    

3. The file will now contain properly encrypted values:
    

​

APP_NAME=myapp

​

LOG_LEVEL=info

​

DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ4dWFsOG...

​

API_KEY=ENC[v1]:eyJzIjoiOXR2Y2FsOG...

​

This approach is perfect when you have mixed environment files with both sensitive and non-sensitive values, and you want precise control over what gets encrypted.

### File Processing Features

- **Preserves formatting**: Maintains indentation, comments, and empty lines
    
- **Handles quotes**: Preserves single and double quotes around values
    
- **Backup support**: Create backups before modification with `--backup`
    
- **Output control**: Write to different file with `--output`
    
- **Error handling**: Detailed error messages for malformed files or encryption failures
    
- **Smart detection**: Automatically detects already-encrypted values to avoid double-encryption
    

## Passphrase Management

EnvSeal supports multiple ways to provide the master passphrase:

### 1. OS Keyring (Recommended)

​

from envseal import store_passphrase_in_keyring

​

​

# Store once

​

store_passphrase_in_keyring("your-master-passphrase")

​

​

# Use automatically

​

passphrase = get_passphrase(PassphraseSource.KEYRING)

​

### 2. Environment Variables

​

export ENVSEAL_PASSPHRASE="your-master-passphrase"

​

​

passphrase = get_passphrase(PassphraseSource.ENV_VAR)

​

### 3. .env Files

Create a separate `.env` file for the passphrase:

​

# .passphrase.env

​

ENVSEAL_PASSPHRASE=your-master-passphrase

​

​

passphrase = get_passphrase(

​

PassphraseSource.DOTENV,

​

dotenv_path=".passphrase.env"

​

)

​

### 4. Hardcoded (Development Only)

​

passphrase = get_passphrase(

​

PassphraseSource.HARDCODED,

​

hardcoded_passphrase="dev-passphrase"

​

)

​

## Security Best Practices

1. **Use OS Keyring**: Store your master passphrase in the OS keyring for maximum security
    
2. **Separate Passphrase Storage**: Never store the passphrase in the same file as encrypted values
    
3. **Environment-Specific Keys**: Use different passphrases for different environments
    
4. **Regular Rotation**: Rotate your master passphrase periodically
    
5. **Access Control**: Limit access to systems that can decrypt your values
    
6. **Backup Strategy**: Always backup your files before bulk encryption operations
    
7. **Selective Encryption**: Use `--prefix-only` mode to encrypt only sensitive values in mixed files
    

## Use Cases

### Initial Setup

​

# 1. Store your master passphrase

​

envseal  store-passphrase  "your-secure-passphrase"

​

​

# 2. Encrypt your existing .env file

​

envseal  seal-file  .env  --backup

​

​

# 3. Your secrets are now encrypted!

​

### Selective Encryption for Mixed Files

​

# 1. Edit your .env file and mark sensitive values

​

# Change: DB_PASSWORD=secret123

​

# To: DB_PASSWORD=ENC[v1]:secret123

​

​

# 2. Encrypt only the marked values

​

envseal  seal-file  .env  --prefix-only  --backup

​

​

# 3. Only marked values are encrypted, others remain plain

​

### Key Rotation

​

# 1. Update your passphrase in keyring

​

envseal  store-passphrase  "new-secure-passphrase"

​

​

# 2. Re-encrypt all encrypted values with new passphrase

​

envseal  seal-file  .env  --backup

​

​

# 3. All encrypted values now use the new passphrase

​

## API Reference

### Core Functions

#### `seal(plaintext, passphrase) -> str`

Encrypt plaintext using AES-GCM.

#### `unseal(token, passphrase) -> bytes`

Decrypt an encrypted token.

#### `seal_file(file_path, passphrase, output_path=None, prefix_only=False) -> int`

Encrypt values in an environment file. Returns the number of values encrypted.

- `prefix_only=True`: Only encrypt values marked with `ENC[v1]:` prefix
    
- `prefix_only=False`: Encrypt all unencrypted values
    

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

​

# Clone repository

​

git  clone  https://github.com/justtil/envseal.git

​

cd  envseal

​

​

# Install in development mode

​

pip  install  -e  ".[dev]"

​

​

# Run tests

​

pytest

​

​

# Format code

​

black  src/  tests/

​

isort  src/  tests/

​

​

# Type checking

​

mypy  src/

​

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

### 0.2.0

- Added `seal-file` command for bulk file encryption
    
- Added `--prefix-only` mode for selective encryption of marked values
    
- Added backup and output file options
    
- Enhanced file processing with quote and formatting preservation
    

### 0.1.0

- Initial release
    
- AES-GCM encryption
    
- Multiple passphrase sources
    
- CLI and library interfaces
    
- python-dotenv integration