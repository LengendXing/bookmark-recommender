from sqlalchemy import String, Text, Integer, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RecommendedRepo(Base, TimestampMixin):
    """AI 推荐的、用户尚未 star 的项目"""
    __tablename__ = "br_recommended_repos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    repo_full_name: Mapped[str] = mapped_column(String(256))
    repo_name: Mapped[str] = mapped_column(String(128))
    owner: Mapped[str] = mapped_column(String(128))
    html_url: Mapped[str] = mapped_column(Text, default="")
    clone_url: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    topics: Mapped[str] = mapped_column(Text, default="")
    ai_tags: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(64), default="")
    language_color: Mapped[str] = mapped_column(String(16), default="")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    license: Mapped[str] = mapped_column(String(64), default="")
    homepage: Mapped[str] = mapped_column(Text, default="")
    default_branch: Mapped[str] = mapped_column(String(64), default="")
    size_kb: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    recommend_reason: Mapped[str] = mapped_column(Text, default="")
    match_tags: Mapped[str] = mapped_column(Text, default="")
    source_tag: Mapped[str] = mapped_column(String(128), default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    recommended_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "repo_full_name", name="uq_user_recommended_repo"),
    )
