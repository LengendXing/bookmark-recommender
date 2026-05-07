from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ExternalApi(Base, TimestampMixin):
    __tablename__ = "br_external_apis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))
    method: Mapped[str] = mapped_column(String(10), index=True)
    path: Mapped[str] = mapped_column(String(512), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    headers: Mapped[str] = mapped_column(Text, default="[]")
    params: Mapped[str] = mapped_column(Text, default="[]")
    script: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_native: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("method", "path", name="uq_ext_api_method_path"),
    )
