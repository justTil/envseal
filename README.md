# EnvSeal

EnvSeal allows you to store encrypted values in your environment files (like `.env`) instead of plain-text secrets. It uses industry-standard AES-GCM encryption and provides flexible options for managing your master passphrase.

## Installation

```bash
pip install envseal
```

## Links

- **Documentation:** [Docs](https://docs.envseal.org/)
- **Source Code:** [GitHub](https://github.com/justTil/envseal)
- **Package:** [PyPI](https://pypi.org/project/envseal/)

## Security Disclaimer

> **⚠️ Important:** While EnvSeal encrypts your secrets, **encrypted environment files should still never be committed to version control systems** like Git, GitHub, GitLab, or any other remote platform.   Even encrypted secrets can pose security risks if exposed publicly.  
> EnvSeal helps prevent the accidental exposure of secrets by protecting against leaks from screenshots, screen-sharing sessions, or unintentional commits to version control.
> **For production environments, always use proper secret management solutions such as:**
>- Cloud-native secret managers (AWS Secrets Manager, Azure Key Vault, Google Secret Manager)
>- Dedicated tools like HashiCorp Vault, Doppler, or Infisical
>- CI/CD platform secret stores (GitHub Secrets, GitLab CI/CD variables)