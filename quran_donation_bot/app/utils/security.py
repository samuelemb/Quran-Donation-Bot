import hashlib
import hmac
import secrets


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    salt, digest = hashed_password.split("$", 1)
    candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, f"{salt}${digest}")
