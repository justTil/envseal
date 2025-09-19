# Getting Started

## Installation and Setup

After installing EnvSeal using pip in your Python environment (venv, conda, or global), you can use EnvSeal simply like any other command in the terminal. If you installed it in a virtual environment, make sure that environment is activated before running EnvSeal commands.

## Quick Start

### Encrypt a Value Using CLI with Keyring (Most Secure)

With your virtual environment (venv or conda) activated, store your passphrase in the system keyring.

> **Important:** Use a unique application name (`APP_NAME`) and key alias (`KEY_ALIAS`) for different projects.
> 
> Reusing the same values is acceptable during development, but for production it's best to choose distinct names to avoid sharing the same passphrase across projects.

Run this command to store your passphrase in the keyring:
```bash
envseal store-passphrase "your-passphrase" --app-name "my-app" --key-alias "my-key"
```

> **Note:** When using custom `APP_NAME` and `KEY_ALIAS` variables, you must specify the same `APP_NAME` and `KEY_ALIAS` used for decryption later in your app. If you don't, **EnvSeal** falls back to its default keyring (if available). This default key would be unable to decrypt your properties, as it was not the key used to encrypt your secrets.

The default values used by the keyring in EnvSeal are as follows:   
- **APP_NAME:** envseal    
- **KEY_ALIAS:** envseal_v1

You can also save a passphrase to the keyring without specifying an app name or key alias (using defaults):
```bash
envseal store-passphrase "your-passphrase"
```

#### Seal Your First Password

Now you can use the following command to seal (encrypt) your password:
```bash
envseal seal "my-database-password"
```

The output will look like this:
```bash
ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ==
```

The encrypted value is a JWT-encoded JSON text that, when decoded, looks like this:
```json
{
  "s": "fSQp+6cKzyeiw16WrmMzsw==",
  "n": "QOqqqx/BPHqFZ2g6",
  "c": "fBNQYby1pqxruW6EDh73OS0cyosS51UWmQUw3U01WVzoZ61w"
}
```

| Field | Name | Description |
|-------|------|-------------|
| `s` | Salt | A random value used to ensure the same input produces different encrypted outputs each time |
| `n` | Nonce | A random value used once per encryption operation to ensure security |
| `c` | Ciphertext | The actual encrypted data |

#### Unseal Your First Password

Now you can use the following command to unseal (decrypt) your password:
```bash
envseal unseal "ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ=="
```

The output will be your database password in plain text:
```bash
my-database-password
```

## Advanced Usage

To find out how to bulk seal/unseal many properties at once and how EnvSeal can be used directly in Python code, go to the Usage section.