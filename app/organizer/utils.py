from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def password_matches_stored(plain_password: str, stored_password: str) -> bool:
    """Argon2 hashes from registration, or legacy plaintext (e.g. seed SQL)."""
    if plain_password is None or stored_password is None:
        return False
    plain = (plain_password or "").strip()
    stored = (stored_password or "").strip()
    if not plain or not stored:
        return False
    if stored.startswith("$"):
        try:
            return password_hash.verify(plain, stored)
        except UnknownHashError:
            return plain == stored
        except Exception:
            return False
    return plain == stored