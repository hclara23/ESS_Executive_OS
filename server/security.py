import base64
import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


PASSWORD_SCHEME = "pbkdf2_sha256"
SECRET_SCHEME = "fernet"
PASSWORD_ITERATIONS = int(os.getenv("ELIO_PASSWORD_ITERATIONS", "600000"))
SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def get_jwt_secret() -> str:
    secret = os.getenv("ELIO_JWT_SECRET", "").strip()
    if len(secret) < 32:
        raise RuntimeError("ELIO_JWT_SECRET must be set and at least 32 characters long.")
    return secret


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def is_password_hash(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(f"{PASSWORD_SCHEME}$")


def _derived_secret_key() -> bytes:
    seed = os.getenv("ELIO_DATA_KEY", "").strip() or get_jwt_secret()
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derived_secret_key())


def is_encrypted_secret(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(f"{SECRET_SCHEME}$")


def encrypt_secret(value: str) -> str:
    if not value:
        raise ValueError("Secret cannot be empty.")
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{SECRET_SCHEME}${token}"


def decrypt_secret(value: str | None) -> str:
    if not value:
        return ""
    if not is_encrypted_secret(value):
        return value
    token = value.split("$", 1)[1]
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Stored secret could not be decrypted with the active data key.") from exc


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored_value: str | None) -> bool:
    if not password or not stored_value:
        return False
    if not is_password_hash(stored_value):
        return hmac.compare_digest(password, stored_value)

    try:
        _, iterations_str, salt_b64, digest_b64 = stored_value.split("$", 3)
        iterations = int(iterations_str)
        salt = _b64decode(salt_b64)
        expected = _b64decode(digest_b64)
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def needs_password_upgrade(stored_value: str | None) -> bool:
    return not is_password_hash(stored_value)


def sanitize_upload_name(filename: str | None, default: str = "upload.bin") -> str:
    candidate = Path(filename or default).name.strip()
    if not candidate:
        candidate = default
    candidate = SAFE_NAME_PATTERN.sub("_", candidate).strip("._")
    if not candidate:
        candidate = default
    return candidate[:120]


def resolve_child_path(base_dir: str | Path, filename: str) -> Path:
    base_path = Path(base_dir).resolve()
    candidate = Path(filename)
    if candidate.name != filename:
        raise ValueError("Nested or absolute paths are not allowed.")
    resolved = (base_path / filename).resolve()
    if resolved.parent != base_path:
        raise ValueError("Path escapes the allowed directory.")
    return resolved
