from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class StarredRepo(Base, TimestampMixin):
    __tablename__ = "br_starred_repos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    account_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repo_full_name: Mapped[str] = mapped_column(String(256), index=True)
    repo_name: Mapped[str] = mapped_column(String(128))
    owner: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(64), default="")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    repo_created_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    repo_updated_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
