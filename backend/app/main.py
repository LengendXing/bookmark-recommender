import asyncio
import concurrent.futures

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import init_db, SessionLocal
from app.services.embedding import train_index

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

settings = get_settings()
setup_logging(settings.ENVIRONMENT)

scheduler = AsyncIOScheduler()


def _sync_api_routes(app: FastAPI):
    """Sync registered routes into database on startup."""
    try:
        import json
        from app.core.database import SessionLocal
        from app.models.api_route import ApiRoute
        from sqlalchemy import select

        skip_prefixes = ("/openapi", "/docs", "/redoc")
        skip_paths = ("/health",)
        db = SessionLocal()
        try:
            for route in app.routes:
                if not hasattr(route, "methods") or not hasattr(route, "path"):
                    continue
                path = route.path
                if path.startswith(skip_prefixes) or path in skip_paths:
                    continue
                for method in route.methods:
                    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        continue
                    existing = db.execute(
                        select(ApiRoute).where(ApiRoute.method == method, ApiRoute.path == path)
                    ).scalar_one_or_none()
                    summary = getattr(route, "summary", "") or ""
                    tags = list(getattr(route, "tags", []))
                    tags_json = json.dumps(tags, ensure_ascii=False)
                    if existing:
                        if existing.source == "manual":
                            continue
                        existing.summary = summary
                        existing.tags = tags_json
                        existing.source = "auto"
                        db.add(existing)
                    else:
                        db.add(ApiRoute(
                            method=method, path=path, summary=summary,
                            tags=tags_json, source="auto",
                        ))
            db.commit()
        finally:
            db.close()
        logger.info("[INIT] API routes synced to database.")
    except Exception as e:
        logger.warning(f"[INIT] API route sync skipped: {e}")


async def _daily_recommendations():
    """Daily cron: generate recommendations for all users with GitHub accounts."""
    logger.info("[CRON] Starting daily recommendation generation...")
    try:
        from app.models.github_account import GitHubAccount
        from sqlalchemy import select

        def _generate_all():
            db = SessionLocal()
            try:
                accounts = db.execute(
                    select(GitHubAccount).where(GitHubAccount.is_deleted == False)
                ).all()
                db.close()

                for (account,) in accounts:
                    try:
                        # Use the recommendation logic from github module
                        from app.api.github import _run_recommendation, _recommendation_progress
                        import threading
                        from datetime import datetime, timezone

                        _recommendation_progress[account.user_id] = {
                            "status": "starting",
                            "total": 0,
                            "current": 0,
                            "message": "Daily auto-recommendation...",
                            "top_tags": [],
                            "found_repos": [],
                            "started_at": datetime.now(timezone.utc).isoformat(),
                        }
                        t = threading.Thread(
                            target=_run_recommendation,
                            args=(account.user_id, 3),
                            daemon=True,
                        )
                        t.start()
                        t.join(timeout=300)  # Max 5 min per user
                    except Exception as e:
                        logger.error(f"[CRON] Recommendation failed for user {account.user_id}: {e}")

            except Exception as e:
                logger.error(f"[CRON] Daily recommendation error: {e}")

        await asyncio.get_event_loop().run_in_executor(_thread_pool, _generate_all)
    except Exception as e:
        logger.error(f"[CRON] Daily recommendation failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _sync_api_routes(app)
    scheduler.add_job(train_index, "interval", hours=1, id="train_index", replace_existing=True)
    scheduler.add_job(_daily_recommendations, "cron", hour=3, minute=0, id="daily_recommendations", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Bookmark Recommender",
    version="0.2.12",
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

from app.api import admin, api_routes, auth, bookmarks, recommend, system_config, github

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(system_config.router, prefix="/api/system-config", tags=["system"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(api_routes.router, prefix="/api/admin/api-routes", tags=["api-routes"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
