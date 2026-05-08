from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    nickname: Optional[str] = None
    avatar_text: Optional[str] = None
    mfa_enabled: bool = False
    created_at: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str
    device_token: Optional[str] = None


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=64)
    avatar_text: Optional[str] = Field(None, max_length=4)
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6, max_length=128)


class MfaConfirm(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class MfaDisable(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=6)


class VerifyRequest(BaseModel):
    code: str
