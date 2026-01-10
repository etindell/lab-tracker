"""Password hashing and verification utilities."""

import secrets
import string

import bcrypt


# Cost factor for bcrypt (2^12 = 4096 iterations)
BCRYPT_ROUNDS = 12

# Bcrypt has a 72-byte limit on passwords
MAX_PASSWORD_BYTES = 72


def _prepare_password(password: str) -> bytes:
    """Prepare password for bcrypt by encoding and truncating.

    Args:
        password: Password string to prepare.

    Returns:
        Password bytes truncated to 72 bytes.
    """
    # Encode to bytes and truncate to bcrypt's limit
    encoded = password.encode("utf-8")
    return encoded[:MAX_PASSWORD_BYTES]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    password_bytes = _prepare_password(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to check against.

    Returns:
        True if password matches, False otherwise.
    """
    password_bytes = _prepare_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        return False


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password.

    Args:
        length: Length of the password. Default is 12.

    Returns:
        Random secure password string.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    # Fill the rest
    password.extend(secrets.choice(alphabet) for _ in range(length - 4))
    # Shuffle to randomize positions
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return "".join(password_list)
