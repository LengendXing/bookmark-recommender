import asyncio
import concurrent.futures

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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
    # 兼容旧数据库，添加缺失列
    try:
        from sqlalchemy import inspect, text
        from app.core.database import engine
        inspector = inspect(engine)
        existing = [c['name'] for c in inspector.get_columns('br_users')]
        new_cols = {
            'nickname': 'TEXT',
            'avatar_text': 'TEXT',
            'mfa_secret': 'TEXT',
            'mfa_enabled': 'BOOLEAN DEFAULT 0',
        }
        for col, ct in new_cols.items():
            if col not in existing:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE br_users ADD COLUMN {col} {ct}"))
                    conn.commit()
                logger.info(f"[DB] Added column br_users.{col}")
    except Exception as e:
        logger.warning(f"[DB] Column migration skipped: {e}")

    _sync_api_routes(app)
    try:
        from app.api.external_apis import register_all_external_routes, seed_native_endpoints
        seed_native_endpoints(app)
        register_all_external_routes(app)
    except Exception as e:
        logger.warning(f"[INIT] External API init skipped: {e}")
    scheduler.add_job(train_index, "interval", hours=1, id="train_index", replace_existing=True)
    scheduler.add_job(_daily_recommendations, "cron", hour=3, minute=0, id="daily_recommendations", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Bookmark Recommender",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import time as _time

@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = _time.time()
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    # Read body for mutation requests
    body_str = ""
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        try:
            body_bytes = await request.body()
            body_str = body_bytes.decode("utf-8", errors="replace")[:4096]
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
        except Exception:
            body_str = "(unable to read body)"

    # Log request
    logger.info(f"[REQ] {method} {path} | client={client_ip} | body={body_str}")

    try:
        response = await call_next(request)
    except Exception as e:
        duration_ms = (_time.time() - start) * 1000
        logger.error(f"[RES] {method} {path} | ERROR | {duration_ms:.0f}ms | client={client_ip} | error={e!r}")
        raise

    duration_ms = (_time.time() - start) * 1000
    status = response.status_code
    level = "ERROR" if status >= 400 else "INFO"
    log_fn = logger.error if status >= 400 else logger.info

    # Extract user from token if present
    user_id = "anon"
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.core.security import decode_access_token
            payload = decode_access_token(auth_header[7:])
            if payload:
                user_id = payload.get("sub", "?")
        except Exception:
            pass

    log_fn(f"[RES] {method} {path} | {status} | {duration_ms:.0f}ms | client={client_ip} | user={user_id}")

    # Fire-and-forget: write call log to database
    if not path.startswith(("/health", "/docs", "/redoc", "/openapi", "/static", "/assets")):
        try:
            from app.core.database import SessionLocal
            from app.models.api_call_log import ApiCallLog
            db = SessionLocal()
            log_entry = ApiCallLog(
                api_id=None,
                method=method,
                path=path,
                request_body=body_str[:4096] if body_str else "",
                response_status=status,
                response_body="",
                duration_ms=round(duration_ms, 2),
                error="" if status < 400 else f"HTTP {status}",
                user_id=None if user_id == "anon" else int(user_id) if user_id.isdigit() else None,
                client_ip=client_ip,
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception:
            pass

    return response

from app.api import admin, api_routes, api_stats, auth, bookmarks, external_apis, recommend, system_config, github

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(system_config.router, prefix="/api/system-config", tags=["system"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(api_routes.router, prefix="/api/admin/api-routes", tags=["api-routes"])
app.include_router(external_apis.router, prefix="/api/admin/external-apis", tags=["external-apis"])
app.include_router(api_stats.router, prefix="/api/admin", tags=["api-stats"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.2"}


# --- Static frontend serving (production) ---
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
_is_prod = os.path.isdir(_static_dir)
if _is_prod:
    app.mount("/assets", StaticFiles(directory=os.path.join(_static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index_path = os.path.join(_static_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"status": "ok", "version": "0.3.2"}
