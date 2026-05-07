from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
import logging

import pyotp

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_mfa_token, verify_mfa_token,
)
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_INTERNAL
from app.schemas.user import UserCreate, LoginRequest, UserOut, ProfileUpdate, MfaConfirm, MfaDisable

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=Response)
def register(body: UserCreate, request: Request, db = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    existing = db.execute(select(User).where((User.username == body.username) | (User.email == body.email))).scalar_one_or_none()
    if existing:
        logger.warning(f"[AUTH] Register failed (duplicate) | username={body.username} | email={body.email} | client={client_ip}")
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Username or email already exists").model_dump_json())

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"[AUTH] Register success | user_id={user.id} | username={user.username} | client={client_ip}")
    return Response.ok(data=UserOut.model_validate(user).model_dump())


@router.post("/login", response_model=Response)
def login(body: LoginRequest, request: Request, db = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    result = db.execute(select(User).where(User.username == body.username)).scalar_one_or_none()
    if result is None or not verify_password(body.password, result.password_hash):
        logger.warning(f"[AUTH] Login failed | username={body.username} | client={client_ip}")
        raise HTTPException(status_code=401, detail=Response.error(ERROR_BAD_REQUEST, "Invalid credentials").model_dump_json())

    if result.mfa_enabled:
        mfa_token = create_mfa_token(result.id)
        logger.info(f"[AUTH] Login requires MFA | user_id={result.id} | username={result.username}")
        return Response.ok(data={"requires_mfa": True, "mfa_token": mfa_token})

    token = create_access_token({"sub": str(result.id)})
    logger.info(f"[AUTH] Login success | user_id={result.id} | username={result.username} | client={client_ip}")
    return Response.ok(data={"token": token, "user": UserOut.model_validate(result).model_dump()})


@router.post("/verify", response_model=Response)
def verify_2fa(body: dict, db = Depends(get_db)):
    mfa_token = body.get("mfa_token", "")
    code = body.get("code", "")
    if not mfa_token or not code or len(code) != 6:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Invalid verification request").model_dump_json())

    user_id = verify_mfa_token(mfa_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail=Response.error(ERROR_BAD_REQUEST, "MFA token expired or invalid").model_dump_json())

    user = db.execute(select(User).where(User.id == user_id, User.is_active)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail=Response.error(ERROR_BAD_REQUEST, "User not found").model_dump_json())

    if not user.mfa_secret or not user.mfa_enabled:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "MFA not configured").model_dump_json())

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code):
        logger.warning(f"[AUTH] MFA verify failed | user_id={user.id}")
        raise HTTPException(status_code=401, detail=Response.error(ERROR_BAD_REQUEST, "Invalid verification code").model_dump_json())

    token = create_access_token({"sub": str(user.id)})
    logger.info(f"[AUTH] MFA verify success | user_id={user.id}")
    return Response.ok(data={"token": token, "user": UserOut.model_validate(user).model_dump()})


@router.get("/me", response_model=Response)
async def me(user: User = Depends(get_current_user)):
    return Response.ok(data=UserOut.model_validate(user).model_dump())


@router.put("/profile", response_model=Response)
def update_profile(body: ProfileUpdate, user: User = Depends(get_current_user), db = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Current password is incorrect").model_dump_json())

    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar_text is not None:
        user.avatar_text = body.avatar_text[:4]
    if body.new_password:
        user.password_hash = hash_password(body.new_password)

    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"[AUTH] Profile updated | user_id={user.id}")
    return Response.ok(data=UserOut.model_validate(user).model_dump())


@router.post("/mfa/setup", response_model=Response)
def mfa_setup(user: User = Depends(get_current_user), db = Depends(get_db)):
    if user.mfa_enabled:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "MFA already enabled").model_dump_json())

    secret = pyotp.random_base32()
    user.mfa_secret = secret
    db.add(user)
    db.commit()

    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        user.username, issuer_name="BookmarkRecommender"
    )
    logger.info(f"[AUTH] MFA setup initiated | user_id={user.id}")
    return Response.ok(data={"secret": secret, "provisioning_uri": provisioning_uri})


@router.post("/mfa/confirm", response_model=Response)
def mfa_confirm(body: MfaConfirm, user: User = Depends(get_current_user), db = Depends(get_db)):
    if not user.mfa_secret:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "MFA setup not initiated").model_dump_json())

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Invalid verification code").model_dump_json())

    user.mfa_enabled = True
    db.add(user)
    db.commit()
    logger.info(f"[AUTH] MFA enabled | user_id={user.id}")
    return Response.ok(data={"mfa_enabled": True})


@router.post("/mfa/disable", response_model=Response)
def mfa_disable(body: MfaDisable, user: User = Depends(get_current_user), db = Depends(get_db)):
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "MFA not enabled").model_dump_json())

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Password incorrect").model_dump_json())

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Invalid verification code").model_dump_json())

    user.mfa_secret = None
    user.mfa_enabled = False
    db.add(user)
    db.commit()
    logger.info(f"[AUTH] MFA disabled | user_id={user.id}")
    return Response.ok(data={"mfa_enabled": False})


@router.get("/mfa/status", response_model=Response)
def mfa_status(user: User = Depends(get_current_user)):
    return Response.ok(data={"mfa_enabled": user.mfa_enabled})
