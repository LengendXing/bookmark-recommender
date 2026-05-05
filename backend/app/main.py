import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.services.embedding import train_index

settings = get_settings()
setup_logging(settings.ENVIRONMENT)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(train_index, "interval", hours=1, id="train_index", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Bookmark Recommender",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, bookmarks, recommend, system_config, collections

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(system_config.router, prefix="/api/system-config", tags=["system"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
