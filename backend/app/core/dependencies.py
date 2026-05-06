from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.config import ERROR_TOKEN_EXPIRED, ERROR_PERMISSION_DENIED
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail=f"{{'code': {ERROR_TOKEN_EXPIRED}, 'message': 'Token expired or invalid'}}")
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail=f"{{'code': {ERROR_PERMISSION_DENIED}, 'message': 'Invalid token'}}")
    result = db.execute(select(User).where(User.id == int(user_id), User.is_active))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail=f"{{'code': {ERROR_PERMISSION_DENIED}, 'message': 'User not found or inactive'}}")
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.id != 1:
        raise HTTPException(status_code=403, detail=f"{{'code': {ERROR_PERMISSION_DENIED}, 'message': 'Permission denied'}}")
    return user
