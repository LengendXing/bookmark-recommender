import secrets

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TrustedDevice(Base, TimestampMixin):
    __tablename__ = "br_trusted_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("br_users.id"), index=True)
    device_token: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=lambda: secrets.token_urlsafe(48))
    device_name: Mapped[str] = mapped_column(String(256))
    ip_address: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(String(512))
    last_used_at: Mapped[str] = mapped_column(server_default="datetime('now')")
    is_deleted: Mapped[bool] = mapped_column(default=False)
