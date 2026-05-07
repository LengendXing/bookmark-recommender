from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ApiRoute(Base, TimestampMixin):
    __tablename__ = "br_api_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(String(10), index=True)
    path: Mapped[str] = mapped_column(String(512), index=True)
    summary: Mapped[str] = mapped_column(String(512), default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    description: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(32), default="auto")

    __table_args__ = (
        UniqueConstraint("method", "path", name="uq_api_route_method_path"),
    )
