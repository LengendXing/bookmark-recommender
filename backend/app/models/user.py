from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "br_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(default=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    avatar_text: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
