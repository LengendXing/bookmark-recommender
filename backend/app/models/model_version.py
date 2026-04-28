from sqlalchemy import String, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "br_model_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64))
    framework: Mapped[str] = mapped_column(String(64), default="")
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    dataset_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="training")
    model_path: Mapped[str] = mapped_column(String(512), default="")
    training_params: Mapped[str] = mapped_column(Text, default="{}")
