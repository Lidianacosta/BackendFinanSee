"""Password hashing and verification utilities.

Provides functions to securely hash user passwords and verify them.
"""

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Hash a plain text password using the recommended algorithm.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed representation of the password.

    """
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: The unhashed password attempt.
        hashed_password: The stored correct hashed password.

    Returns:
        True if the password matches, False otherwise.

    """
    return _password_hash.verify(plain_password, hashed_password)
