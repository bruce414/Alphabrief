from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from passlib.context import CryptContext

from app.core.config import get_settings


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padded = raw + "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _sign(data: bytes, secret_key: str) -> str:
    sig = hmac.new(secret_key.encode("utf-8"), data, hashlib.sha256).digest()
    return _b64url_encode(sig)


@dataclass(frozen=True)
class SessionClaims:
    user_id: UUID
    expires_at: datetime


def create_session_token(*, user_id: UUID, expires_at: datetime) -> str:
    settings = get_settings()
    payload = {
        "uid": str(user_id),
        "exp": int(expires_at.timestamp()),
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_raw).encode("ascii")
    sig = _sign(payload_b64, settings.secret_key)
    return f"{payload_b64.decode('ascii')}.{sig}"


def verify_session_token(token: str) -> SessionClaims | None:
    settings = get_settings()
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None

    expected = _sign(payload_b64.encode("ascii"), settings.secret_key)
    if not hmac.compare_digest(sig, expected):
        return None

    try:
        payload: dict[str, Any] = json.loads(_b64url_decode(payload_b64))
        uid = UUID(payload["uid"])
        exp = int(payload["exp"])
    except Exception:
        return None

    expires_at = datetime.fromtimestamp(exp, tz=UTC)
    if datetime.now(UTC) >= expires_at:
        return None

    return SessionClaims(user_id=uid, expires_at=expires_at)


def session_expiry_from_now() -> datetime:
    return datetime.now(UTC) + timedelta(days=30)

