from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode('utf-8')
    h_bytes = hashed.encode('utf-8') if isinstance(hashed, str) else hashed
    return bcrypt.checkpw(pwd_bytes, h_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def create_mfa_token(user_id: int) -> str:
    return create_access_token({"sub": str(user_id), "scope": "mfa"}, timedelta(minutes=5))


def verify_mfa_token(token: str) -> Optional[int]:
    payload = decode_access_token(token)
    if payload is None or payload.get("scope") != "mfa":
        return None
    return int(payload["sub"])
