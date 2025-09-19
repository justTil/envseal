# Usage

EnvSeal is a tool for securely encrypting sensitive values in environment files. It helps protect secrets like database passwords, API keys, and tokens while keeping your configuration files readable and version-control friendly.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Concepts](#basic-concepts)
3. [Command Line Usage](#command-line-usage)
4. [Python Library Usage](#python-library-usage)
5. [Passphrase Management](#passphrase-management)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)

## Quick Start

### 1. Set Up Your Master Passphrase

Please go to the "Getting Started" page

### 2. Encrypt Your Environment File

Encrypt **all** values in your `.env` file:

```bash
envseal seal-file .env --backup
```

**Before encryption:**
```env
DB_PASSWORD=mypassword123
API_TOKEN=sk-1234567890abcdef
PORT=3000
```

**After encryption:**
```env
DB_PASSWORD=ENC[v1]:eyJzIjogIjVaZ0I3L3A0L05y...
API_TOKEN=ENC[v1]:eyJzIjogIm1IL1haTjd3VW...
PORT=ENC[v1]:eyJzIjogIktRamJYMGNVWkxGN1JW...
```
> Running this command will seal every value in the file. Later, you'll learn how to specify exactly which values to seal and which to leave unsealed.

### 3. Use in Your Application

```python
from envseal import load_sealed_env, PassphraseSource

# Load and decrypt environment variables
env_vars = load_sealed_env(
    dotenv_path=".env", passphrase_source=PassphraseSource.KEYRING
)

# Access decrypted values
db_password = env_vars["DB_PASSWORD"]  # Returns: mypassword123
api_token = env_vars["API_TOKEN"]  # Returns: sk-1234567890abcdef
port = env_vars["PORT"]  # Returns: 3000
print(f"DB_PASSWORD: {db_password}, API_TOKEN: {api_token}, PORT: {port}")
```

## Basic Concepts

### How EnvSeal Works

EnvSeal uses symmetric encryption to protect individual values in your environment files. Each encrypted value is prefixed with `ENC[v1]:` to indicate it's encrypted and specify the encryption version.

**Key Features:**   
- Encrypts only the values, not the entire file  
- Preserves file structure, comments, and formatting  
- Version-controlled friendly (encrypted values are deterministic)  
- Supports selective encryption for mixed sensitive/non-sensitive files  

### Encryption Format

Encrypted values follow this format:
```
VARIABLE_NAME=ENC[v1]:base64EncodedEncryptedData
```

The `ENC[v1]:` prefix tells EnvSeal this value is encrypted and which version of the encryption scheme to use.

## Command Line Usage

### Encrypting Files

#### Encrypt All Values

Encrypt every unencrypted value in a file:

```bash
envseal seal-file .env
```

#### Selective Encryption

Only encrypt values you've marked with the `ENC[v1]:` prefix:

```bash
envseal seal-file .env --prefix-only
```

**Workflow for selective encryption:**

1. Mark sensitive values in your `.env` file:
   ```env
   # Non-sensitive values (will not be encrypted)
   APP_NAME=myapp
   LOG_LEVEL=info
   PORT=3000
   
   # Sensitive values (mark with ENC[v1]: prefix)
   DB_PASSWORD=ENC[v1]:mypassword123
   API_KEY=ENC[v1]:sk-1234567890abcdef
   ```

2. Run the encryption command:
   ```bash
   envseal seal-file .env --prefix-only
   ```

3. Result:
   ```env
   # Non-sensitive values remain unchanged
   APP_NAME=myapp
   LOG_LEVEL=info
   PORT=3000
   
   # Sensitive values are now encrypted
   DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ4dWFsOG...
   API_KEY=ENC[v1]:eyJzIjoiOXR2Y2FsOG...
   ```

#### Advanced Options

**Create backup before modifying:**
```bash
envseal seal-file .env --backup
```

**Save to a different file:**
```bash
envseal seal-file .env --output .env.encrypted
```

### Decrypting Files

#### Decrypt Entire File

```bash
envseal unseal-file .env
```

#### Decrypt with Options

```bash
# Create backup before decrypting
envseal unseal-file .env --backup

# Save decrypted version to new file
envseal unseal-file .env --output .env.decrypted

# Only decrypt values with ENC[v1]: prefix
envseal unseal-file .env --prefix-only
```

### Loading Environment Variables

#### Display Decrypted Values

```bash
envseal load-env --env-file=.env
```

#### Apply to Current Shell Environment

```bash
envseal load-env --env-file=.env --apply
```

## Python Library Usage

### Basic Encryption and Decryption

```python
from envseal import seal, unseal, get_passphrase, PassphraseSource

# Get your master passphrase
passphrase = get_passphrase(PassphraseSource.KEYRING)

# Encrypt a single value
encrypted_token = seal("my-secret-value", passphrase)
print(encrypted_token)  # ENC[v1]:eyJzIjoiNnZ...

# Decrypt the value
decrypted_bytes = unseal(encrypted_token, passphrase)
print(decrypted_bytes.decode())  # my-secret-value
```

### File Operations

#### Encrypting Files Programmatically

```python
from envseal import seal_file, get_passphrase, PassphraseSource

# Get passphrase
passphrase = get_passphrase(PassphraseSource.KEYRING)

# Encrypt all values in a file
modified_count = seal_file(
    file_path=".env",
    passphrase=passphrase,
    prefix_only=False,  # Encrypt all values
)
print(f"Encrypted {modified_count} values")

# Only encrypt marked values
modified_count = seal_file(
    file_path=".env",
    passphrase=passphrase,
    prefix_only=True,  # Only encrypt values with ENC[v1]: prefix
)
print(f"Encrypted {modified_count} marked values")
print("Done")
```

#### Loading Environment Files

```python
from envseal import load_sealed_env, PassphraseSource

# Load and automatically decrypt environment variables
env_vars = load_sealed_env(
    dotenv_path=".env", passphrase_source=PassphraseSource.KEYRING
)

# Access values (automatically decrypted)
db_password = env_vars.get("DB_PASSWORD")
api_key = env_vars.get("API_KEY")
print(f"DB_PASSWORD: {db_password}, API_KEY: {api_key}")
```

#### Direct Integration with os.environ

```python
import os
from envseal import apply_sealed_env, PassphraseSource

# Load encrypted .env file directly into os.environ
apply_sealed_env(".env", PassphraseSource.KEYRING)

# Access values normally
db_password = os.environ["DB_PASSWORD"]
api_key = os.environ["API_KEY"]
print(f"DB_PASSWORD: {db_password}, API_KEY: {api_key}")
```
> This will load encrypted values to os.environ. Helpful if os.getenv() is used, as you can use envseal to then unseal the env.

### Integration with python-dotenv

```python
import os
from dotenv import load_dotenv
from envseal import unseal, get_passphrase, PassphraseSource

# Load .env file using python-dotenv
load_dotenv()

# Get passphrase for decryption
passphrase = get_passphrase(PassphraseSource.KEYRING)

# Manually decrypt specific values
raw_password = os.environ["DB_PASSWORD"]
if raw_password.startswith("ENC[v1]:"):
    db_password = unseal(raw_password, passphrase).decode()
    print(f"DB_PASSWORD: {db_password}")
else:
    db_password = raw_password
```

## Passphrase Management

EnvSeal supports multiple methods for managing your master passphrase:

### 1. OS Keyring (Recommended)

The most secure option for local development:

```python
from envseal import store_passphrase_in_keyring, get_passphrase, PassphraseSource

# Store passphrase once
store_passphrase_in_keyring("your-master-passphrase")

# Use automatically in your applications
passphrase = get_passphrase(PassphraseSource.KEYRING)
print(f"Retrieved passphrase: {passphrase}")
# Passphrase is still in bytes, decode when needed
print(f"Decoded passphrase: {passphrase.decode()}")
```

### 2. Environment Variables

Good for CI/CD environments:

```bash
export ENVSEAL_PASSPHRASE="your-master-passphrase"
```

```python
from envseal import get_passphrase, PassphraseSource

passphrase = get_passphrase(PassphraseSource.ENV_VAR)
print(f"Retrieved passphrase: {passphrase}")
print(f"Decoded passphrase: {passphrase.decode()}")
```

Or use a custom environment variable name
```bash
export MY_CUSTOM_PASSPHRASE="this-is-very-custom"
```
```python
from envseal import get_passphrase, PassphraseSource

passphrase = get_passphrase(
    PassphraseSource.ENV_VAR, env_var_name="MY_CUSTOM_PASSPHRASE"
)
print(f"Retrieved passphrase: {passphrase}")
print(f"Decoded passphrase: {passphrase.decode()}")
```

### 3. Separate .env File

Store the passphrase in a separate, untracked file:

```bash
# .secrets.env (add to .gitignore)
MASTER_KEY=your-master-passphrase
```

```python
from envseal import get_passphrase

passphrase = get_passphrase(dotenv_path=".secrets.env", dotenv_var_name="MASTER_KEY")
print(f"Retrieved passphrase: {passphrase}")
print(f"Decoded passphrase: {passphrase.decode()}")
```

### 4. Interactive Prompt

Prompt the user to enter the passphrase:

```python
from envseal import get_passphrase, PassphraseSource

# Will prompt user to type passphrase securely
passphrase = get_passphrase(PassphraseSource.PROMPT)
print(f"Retrieved passphrase: {passphrase}")
print(f"Decoded passphrase: {passphrase.decode()}")
```

### 5. Hardcoded (Development Only)

**Warning:** Only use this for development/testing, never in production:

```python
from envseal import get_passphrase, PassphraseSource

passphrase = get_passphrase(
    PassphraseSource.HARDCODED, hardcoded_passphrase="dev-passphrase"
)
print(f"Retrieved passphrase: {passphrase}")
print(f"Decoded passphrase: {passphrase.decode()}")
```

## Advanced Features

### File Processing Features

EnvSeal preserves your file structure and formatting:

- **Maintains formatting**: Keeps indentation, comments, and empty lines
- **Handles quotes**: Preserves single and double quotes around values
- **Smart detection**: Automatically detects already-encrypted values to avoid double-encryption
- **Error handling**: Provides detailed error messages for malformed files or encryption failures

Example of preserved formatting:
```env
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=ENC[v1]:eyJzIjoiNnZ4dWFsOG...  # This will be encrypted

# API Configuration  
API_BASE_URL="https://api.example.com"
API_KEY=ENC[v1]:eyJzIjoiOXR2Y2FsOG...
```

### Key Rotation
Coming soon

### Encryption Modes Comparison

| Mode | Command | Behavior |
|------|---------|----------|
| **Standard** | `seal-file .env` | Encrypts all unencrypted values |
| **Prefix-only** | `seal-file .env --prefix-only` | Only encrypts values marked with `ENC[v1]:` |

**Standard Mode Example:**
```env
# Before
DATABASE_URL=postgresql://user:secret@localhost/db
API_KEY=abc123
ALREADY_SEALED=ENC[v1]:eyJzIjoiNnZ...

# After
DATABASE_URL=ENC[v1]:eyJzIjoiOXR...
API_KEY=ENC[v1]:eyJzIjoiNnZ...
ALREADY_SEALED=ENC[v1]:eyJzIjoiNnZ...  # Unchanged
```

**Prefix-only Mode Example:**
```env
# Before (manually mark values to encrypt)
DATABASE_URL=postgresql://user:secret@localhost/db
API_KEY=abc123
DB_PASSWORD=ENC[v1]:my-secret-password
PORT=ENC[v1]:5432

# After
DATABASE_URL=postgresql://user:secret@localhost/db  # Unchanged
API_KEY=abc123                                      # Unchanged
DB_PASSWORD=ENC[v1]:eyJzIjoiOXR...                  # Encrypted
PORT=ENC[v1]:eyJzIjoiNnZ...                         # Encrypted
```

## Best Practices

### Security Best Practices

1. **Use OS Keyring for local development**: Most secure option for storing your master passphrase
2. **Use environment variables in CI/CD**: Set `ENVSEAL_PASSPHRASE` in your deployment pipeline
3. **Never commit passphrases**: Add passphrase files to `.gitignore`
4. **Rotate keys periodically**: Update your master passphrase regularly
5. **Use selective encryption**: Only encrypt sensitive values, leave configuration values plain

### File Organization

```bash
# Recommended file structure
.env                    # Encrypted sensitive values
.env.example           # Template with placeholder values
.secrets.env           # Passphrase storage (in .gitignore)
.gitignore             # Include .secrets.env
```

### Example .gitignore

```gitignore
# Environment files with real secrets
.secrets.env
.env.local
.env
```
> Never upload sealed properties. While EnvSeal helps prevent accidental leaks of sensitive values like API keys and passwords, it's still crucial to avoid uploading them to any remote platform that isn't your designated secret manager.
