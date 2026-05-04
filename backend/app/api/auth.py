from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_INTERNAL
from app.schemas.user import UserCreate, LoginRequest, UserOut

router = APIRouter()


@router.post("/register", response_model=Response)
def register(body: UserCreate, db = Depends(get_db)):
    existing = db.execute(select(User).where((User.username == body.username) | (User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Username or email already exists").model_dump_json())

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Response.ok(data=UserOut.model_validate(user).model_dump())


@router.post("/login", response_model=Response)
def login(body: LoginRequest, db = Depends(get_db)):
    result = db.execute(select(User).where(User.username == body.username)).scalar_one_or_none()
    if result is None or not verify_password(body.password, result.password_hash):
        raise HTTPException(status_code=401, detail=Response.error(ERROR_BAD_REQUEST, "Invalid credentials").model_dump_json())

    token = create_access_token({"sub": str(result.id)})
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
