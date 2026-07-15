import hashlib
import hmac
import os
from .config import settings


def hash_password(password: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    computed_hash = hash_password(plain_password)
    return hmac.compare_digest(computed_hash, stored_hash)