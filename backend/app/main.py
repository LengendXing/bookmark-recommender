import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

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
    version="0.2.9",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_push_body(request: Request, call_next):
    if request.url.path.endswith("/push") and request.method == "POST":
        body = await request.body()
        logger.info(f"[PUSH REQUEST] Body: {body.decode()[:2000]}")
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    response = await call_next(request)
    return response

from app.api import admin, auth, bookmarks, recommend, system_config, collections, github

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(system_config.router, prefix="/api/system-config", tags=["system"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(github.router, prefix="/api/github", tags=["github"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
