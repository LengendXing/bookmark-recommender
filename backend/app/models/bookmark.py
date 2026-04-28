from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Bookmark(Base, TimestampMixin):
    __tablename__ = "br_bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(128), default="")
    content_preview: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    rating: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[str] = mapped_column("metadata", Text, default="{}")
    user_id: Mapped[int] = mapped_column(Integer, index=True)
