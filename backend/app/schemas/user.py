from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class VerifyRequest(BaseModel):
    code: str = Field(min_length=4, max_length=12)
