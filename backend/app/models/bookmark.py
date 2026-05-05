from sqlalchemy import String, Text, Integer
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
    collection_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    # Extended fields for AI-powered import
    folder_path: Mapped[str] = mapped_column(String(512), default="")
    date_added: Mapped[str] = mapped_column(String(64), default="")
    page_title: Mapped[str] = mapped_column(Text, default="")
    page_description: Mapped[str] = mapped_column(Text, default="")
    page_text: Mapped[str] = mapped_column(Text, default="")
    generated_title: Mapped[str] = mapped_column(Text, default="")
    generated_description: Mapped[str] = mapped_column(Text, default="")
    crawl_error: Mapped[str] = mapped_column(Text, default="")
