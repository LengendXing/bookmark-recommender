from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GitHubAccount(Base, TimestampMixin):
    __tablename__ = "br_github_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    github_login: Mapped[str] = mapped_column(String(128))
    avatar_url: Mapped[str] = mapped_column(Text, default="")
    token: Mapped[str] = mapped_column(String(256))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
