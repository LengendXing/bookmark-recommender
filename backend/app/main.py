from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import init_db

settings = get_settings()
setup_logging(settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Bookmark Recommender",
    version=getattr(__import__("app"), "__version__", "0.1.0"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Import routers here as Phase progresses
# from app.api import auth, bookmarks, recommend
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
# app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
