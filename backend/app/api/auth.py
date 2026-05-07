from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_INTERNAL
from app.schemas.user import UserCreate, LoginRequest, UserOut

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

    token = create_access_token({"sub": str(result.id)})
    logger.info(f"[AUTH] Login success | user_id={result.id} | username={result.username} | client={client_ip}")
    return Response.ok(data={"token": token, "user": UserOut.model_validate(result).model_dump()})


@router.get("/me", response_model=Response)
async def me(user: User = Depends(get_current_user)):
    return Response.ok(data=UserOut.model_validate(user).model_dump())


@router.post("/verify", response_model=Response)
async def verify_2fa(body: dict, user: User = Depends(get_current_user)):
    code = body.get("code", "")
    if not code or len(code) < 4:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Invalid verification code").model_dump_json())
    return Response.ok(data={"verified": True})
