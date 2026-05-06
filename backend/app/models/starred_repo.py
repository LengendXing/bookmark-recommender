from sqlalchemy import String, Text, Integer, Boolean
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
    language_color: Mapped[str] = mapped_column(String(16), default="")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    size_kb: Mapped[int] = mapped_column(Integer, default=0)
    topics: Mapped[str] = mapped_column(Text, default="")
    homepage: Mapped[str] = mapped_column(Text, default="")
    license: Mapped[str] = mapped_column(String(64), default="")
    default_branch: Mapped[str] = mapped_column(String(64), default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    readme_text: Mapped[str] = mapped_column(Text, default="")
    repo_created_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    repo_updated_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_tags: Mapped[str] = mapped_column(Text, default="")
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    ai_category: Mapped[str] = mapped_column(String(64), default="")
    ai_analyzed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analyze_error: Mapped[str] = mapped_column(Text, default="")
