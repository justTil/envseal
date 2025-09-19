"""
EnvSeal Usage Examples

This file demonstrates various ways to use EnvSeal in your Python applications.
"""

import os
import tempfile

from envseal import (
    seal,
    unseal,
    get_passphrase,
    load_sealed_env,
    apply_sealed_env,
    PassphraseSource,
)


def example_basic_encrypt_decrypt():
    """Basic encryption and decryption example"""
    print("=== Basic Encrypt/Decrypt Example ===")

    # Get passphrase (you would typically use keyring or env var)
    passphrase = get_passphrase(
        PassphraseSource.HARDCODED, hardcoded_passphrase="my-secret-passphrase"
    )

    # Encrypt a secret
    secret_data = "my-database-password"
    encrypted_token = seal(secret_data, passphrase)

    print(f"Original: {secret_data}")
    print(f"Encrypted: {encrypted_token}")

    # Decrypt the secret
    decrypted_bytes = unseal(encrypted_token, passphrase)
    decrypted_data = decrypted_bytes.decode()

    print(f"Decrypted: {decrypted_data}")
    print(f"Match: {secret_data == decrypted_data}")
    print()


def example_dotenv_integration():
    """Example of .env file integration"""
    print("=== .env Integration Example ===")

    # Create some encrypted values
    passphrase = get_passphrase(
        PassphraseSource.HARDCODED, hardcoded_passphrase="env-example-passphrase"
    )

    db_password = seal("super-secret-db-password", passphrase)
    api_key = seal("sk-1234567890abcdef", passphrase)

    # Create a temporary .env file
    env_content = f"""
# Application Configuration
APP_NAME=MyAwesomeApp
DEBUG=true
PORT=8000

# Encrypted Secrets
DATABASE_PASSWORD={db_password}
API_KEY={api_key}

# Plain text (non-sensitive)
LOG_LEVEL=INFO
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content.strip())
        env_path = f.name

    try:
        # Load environment variables with automatic decryption
        env_vars = load_sealed_env(
            dotenv_path=env_path,
            passphrase_source=PassphraseSource.HARDCODED,
            hardcoded_passphrase="env-example-passphrase",
        )

        print("Loaded environment variables:")
        for key, value in env_vars.items():
            # Don't print actual secrets in example
            if "PASSWORD" in key or "KEY" in key:
                print(f"  {key}=<decrypted secret>")
            else:
                print(f"  {key}={value}")

        # Verify decryption worked
        assert env_vars["DATABASE_PASSWORD"] == "super-secret-db-password"
        assert env_vars["API_KEY"] == "sk-1234567890abcdef"
        print("✓ All secrets decrypted successfully!")

    finally:
        os.unlink(env_path)

    print()


def example_different_passphrase_sources():
    """Example showing different passphrase sources"""
    print("=== Different Passphrase Sources Example ===")

    # 1. Hardcoded (for development only)
    print("1. Hardcoded passphrase:")
    passphrase1 = get_passphrase(
        PassphraseSource.HARDCODED, hardcoded_passphrase="hardcoded-example"
    )
    print(f"   Got passphrase: {len(passphrase1)} bytes")

    # 2. Environment variable
    print("2. Environment variable:")
    os.environ["EXAMPLE_PASSPHRASE"] = "env-var-example"
    try:
        passphrase2 = get_passphrase(
            PassphraseSource.ENV_VAR, env_var_name="EXAMPLE_PASSPHRASE"
        )
        print(f"   Got passphrase: {len(passphrase2)} bytes")
    finally:
        del os.environ["EXAMPLE_PASSPHRASE"]

    # 3. .env file
    print("3. .env file:")
    passphrase_env_content = "MASTER_PASSPHRASE=dotenv-example"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(passphrase_env_content)
        passphrase_env_path = f.name

    try:
        passphrase3 = get_passphrase(
            PassphraseSource.DOTENV,
            dotenv_path=passphrase_env_path,
            dotenv_var_name="MASTER_PASSPHRASE",
        )
        print(f"   Got passphrase: {len(passphrase3)} bytes")
    finally:
        os.unlink(passphrase_env_path)

    print()


def example_apply_to_environ():
    """Example of applying sealed variables to os.environ"""
    print("=== Apply to os.environ Example ===")

    # Store original values to restore later
    original_vars = {}
    test_vars = ["EXAMPLE_DB_URL", "EXAMPLE_SECRET"]

    for var in test_vars:
        if var in os.environ:
            original_vars[var] = os.environ[var]
            del os.environ[var]

    try:
        # Create encrypted values
        passphrase = get_passphrase(
            PassphraseSource.HARDCODED, hardcoded_passphrase="environ-example"
        )

        db_url = seal("postgresql://user:pass@localhost/mydb", passphrase)
        secret_key = seal("super-secret-key-12345", passphrase)

        # Create .env file
        env_content = f"""
EXAMPLE_DB_URL={db_url}
EXAMPLE_SECRET={secret_key}
EXAMPLE_DEBUG=true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content.strip())
            env_path = f.name

        try:
            # Apply to os.environ
            apply_sealed_env(
                dotenv_path=env_path,
                passphrase_source=PassphraseSource.HARDCODED,
                hardcoded_passphrase="environ-example",
            )

            print("Variables applied to os.environ:")
            print(f"  EXAMPLE_DB_URL=<decrypted database url>")
            print(f"  EXAMPLE_SECRET=<decrypted secret key>")
            print(f"  EXAMPLE_DEBUG={os.environ.get('EXAMPLE_DEBUG')}")

            # Verify they're actually decrypted
            assert (
                os.environ["EXAMPLE_DB_URL"] == "postgresql://user:pass@localhost/mydb"
            )
            assert os.environ["EXAMPLE_SECRET"] == "super-secret-key-12345"
            print("✓ All variables successfully applied and decrypted!")

        finally:
            os.unlink(env_path)
            # Clean up test variables
            for var in test_vars + ["EXAMPLE_DEBUG"]:
                if var in os.environ:
                    del os.environ[var]

    finally:
        # Restore original values
        for var, value in original_vars.items():
            os.environ[var] = value

    print()


def example_error_handling():
    """Example of error handling"""
    print("=== Error Handling Example ===")

    passphrase1 = b"correct-passphrase"
    passphrase2 = b"wrong-passphrase"

    # Create encrypted token
    token = seal("secret-data", passphrase1)

    # Try to decrypt with wrong passphrase
    try:
        unseal(token, passphrase2)
        print("ERROR: Should have failed!")
    except Exception as e:
        print(f"✓ Correctly caught error: {e}")

    # Try invalid token format
    try:
        unseal("invalid-token", passphrase1)
        print("ERROR: Should have failed!")
    except Exception as e:
        print(f"✓ Correctly caught error: {e}")

    print()


def example_web_framework_integration():
    """Example of web framework integration patterns"""
    print("=== Web Framework Integration Example ===")

    # Django-style settings
    print("Django-style integration:")
    print("""
# In your settings.py
from envseal import apply_sealed_env, PassphraseSource

# Apply sealed environment variables at startup
apply_sealed_env(
    dotenv_path=".env",
    passphrase_source=PassphraseSource.KEYRING
)

# Use environment variables normally
SECRET_KEY = os.environ["SECRET_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
""")

    # FastAPI/Pydantic-style settings
    print("FastAPI/Pydantic-style integration:")
    print("""
# In your config.py
from pydantic import BaseSettings
from envseal import load_sealed_env, PassphraseSource

class Settings(BaseSettings):
    secret_key: str
    database_url: str
    
    class Config:
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
""")

    print()


if __name__ == "__main__":
    print("EnvSeal Usage Examples")
    print("=" * 50)
    print()

    # Run all examples
    example_basic_encrypt_decrypt()
    example_dotenv_integration()
    example_different_passphrase_sources()
    example_apply_to_environ()
    example_error_handling()
    example_web_framework_integration()

    print("All examples completed successfully! 🎉")
    print()
    print("Next steps:")
    print("1. Install envseal: pip install envseal")
    print("2. Store your passphrase: envseal store-passphrase 'your-master-passphrase'")
    print("3. Encrypt secrets: envseal seal 'your-secret-value'")
    print("4. Add encrypted values to your .env file")
    print("5. Use load_sealed_env() in your application")
