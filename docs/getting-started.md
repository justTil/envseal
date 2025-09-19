# Getting started

## Quick Start

### Encrypt a value using CLI with keyring (most secure)
​With your virtual environment (venv or conda) activated, store your passphrase in the system keyring.  

> Use a unique application name (`APP_NAME`) and key alias (`KEY_ALIAS`) for different projects.    
> 
> Reusing the same values is acceptable during development, but for production it’s best to choose distinct names to avoid sharing the same passphrase across projects.

Run this command to store your passphrase in the keyring:
```bash
envseal store-passphrase "your-passphrase" --app-name "my-app" --key-alias "my-key"
```
> When using custom APP_NAME and KEY_ALIAS variables, you must specify the `APP_NAME` and `KEY_ALIAS` used for decryption later in your app. If you don’t, **envseal** falls back to its default keyring (if available). This key would be unable to decrypt your properties, as it was not the key used to encrypt your secrets.


The default values used by a keyring in envseal are as follows:  
- APP_NAME: envseal  
- KEY_ALIAS: envseal_v1

Save passphrase to keyring without specifying an app name or key alias (using defaults):
```bash
envseal store-passphrase "your-passphrase"
```

#### Seal your first password
Now you can use the following command to seal (encrypt) your password:
```bash
envseal seal "my-database-password"
```
The output will look like this:
```bash    
ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ==
```
The encrypted value is a jwt encoded json text that, decoded, looks likes this:
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

#### Unseal your first password
Now you can use the following command to seal (encrypt) your password:
```bash
envseal unseal "ENC[v1]:eyJzIjogImZTUXArNmNLenllaXcxNldybU16c3c9PSIsICJuIjogIlFPcXFxeC9CUEhxRloyZzYiLCAiYyI6ICJmQk5RWWJ5MXBxeHJ1VzZFRGg3M09TMGN5b3NTNTFVV21RVXczVTAxV1Z6b1o2MXcifQ=="
```
The output will be our database password in plain text:
```bash    
my-database-password
```

## Advanced Usage
Find out how to builk seal/unseal many properties at once and how envseal can be used in
python code directly, go to Usage