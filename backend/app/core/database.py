from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://"),
    echo=settings.ENVIRONMENT == "development",
    connect_args={"check_same_thread": False, "timeout": 30}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
