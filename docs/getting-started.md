# Getting Started

## Installation and Setup

After installing EnvSeal via pip, you can use it as a standard command-line tool. If you installed it in a virtual environment, ensure the environment is activated before running EnvSeal commands.

---

## Quick Start

### Encrypting Your First Value

The most secure approach is to use EnvSeal with your system's keyring for passphrase management.

#### Step 1: Store Your Passphrase

Store your passphrase securely in the system keyring:
```bash
envseal store-passphrase "your-passphrase" --app-name "my-app" --key-alias "my-key"
```

!!! tip "Best Practices for App Names and Key Aliases"
    - Use unique `APP_NAME` and `KEY_ALIAS` values for different projects
    - Reusing values during development is acceptable
    - In production, use distinct names to avoid sharing passphrases across projects

!!! warning "Remember Your Configuration"
    When using custom `APP_NAME` and `KEY_ALIAS`, you **must** specify the same values during decryption. Otherwise, EnvSeal falls back to the default keyring, which cannot decrypt values encrypted with a different key.

**Default keyring values:**

- **APP_NAME:** `envseal`
- **KEY_ALIAS:** `envseal_v1`

To use the default values, simply omit the flags:
```bash
envseal store-passphrase "your-passphrase"
```

#### Step 2: Encrypt a Value

Encrypt your first secret using the `seal` command:
```bash
envseal seal "my-database-password"
```

**Output:**
```
ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ==
```

The encrypted output is a base64-encoded JSON payload containing:

| Field | Name       | Description |
|-------|------------|-------------|
| `s`   | Salt       | Random value ensuring unique encrypted outputs for identical inputs |
| `n`   | Nonce      | Single-use random value providing additional security per operation |
| `c`   | Ciphertext | The encrypted data |

??? example "Decoded Structure"
    When decoded, the encrypted value contains:
```json
    {
      "s": "fSQp+6cKzyeiw16WrmMzsw==",
      "n": "QOqqqx/BPHqFZ2g6",
      "c": "fBNQYby1pqxruW6EDh73OS0cyosS51UWmQUw3U01WVzoZ61w"
    }
```

#### Step 3: Decrypt a Value

Decrypt the value using the `unseal` command:
```bash
envseal unseal "ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ=="
```

**Output:**
```
my-database-password
```

---

## Alternative: Using Environment Variables

For environments where keyring access is unavailable, you can provide the passphrase via an environment variable:
```bash
export ENVSEAL_PASSPHRASE="my-super-secret-passphrase"
envseal seal "my-database-password" --passphrase-source=env_var
```

!!! warning "Security Consideration"
    Environment variables are less secure than keyring storage. Use this method only when keyring access is not available.

---

## Next Steps

Ready to explore more features? Learn how to:

- Bulk encrypt and decrypt multiple values at once
- Integrate EnvSeal directly into your Python code
- Configure advanced encryption options

Continue to the [Usage](usage.md) section for detailed instructions.