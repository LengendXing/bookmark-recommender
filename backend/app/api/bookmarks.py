import json
import secrets
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.database import SessionLocal, get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND, ERROR_PERMISSION_DENIED
from app.schemas.bookmark import BatchDeleteRequest, BookmarkCreate, BookmarkOut, BookmarkUpdate
from app.services.ingest import ingest_bulk, ingest_single
from app.services.ai_service import analyze_bookmark
from app.services.import_service import import_bookmarks_with_ai
from app.services.scraper import scrape_page_sync

router = APIRouter()


@router.post("/ingest", response_model=Response)
def ingest(
    body: dict,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "URL required").model_dump_json())

    bm = ingest_single(db, url, user.id)
    tags = _parse_tags(bm.tags)
    return Response.ok(data=_to_out(bm, tags).model_dump())
@router.post("/ingest-bulk", response_model=Response)
def ingest_bulk_endpoint(
    body: dict,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    urls = body.get("urls", [])
    if not urls:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "urls array required").model_dump_json())

    bookmarks = ingest_bulk(db, urls, user.id)
    data = []
    for bm in bookmarks:
        tags = _parse_tags(bm.tags)
        data.append(_to_out(bm, tags).model_dump())
    return Response.ok(data=data)


@router.post("", response_model=Response)
def create_bookmark(
    body: BookmarkCreate,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bm = Bookmark(
        title=body.title,
        url=body.url,
        description=body.description,
        author=body.author,
        category=body.category,
        tags=json.dumps(body.tags, ensure_ascii=False),
        user_id=user.id,
    )
    db.add(bm)
    db.commit()
    db.refresh(bm)
    return Response.ok(data=_to_out(bm, body.tags).model_dump())


@router.get("", response_model=Response)
def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Search title/description"),
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Bookmark).where(Bookmark.user_id == user.id)
    if search:
        q = q.where(
            (Bookmark.title.ilike(f"%{search}%")) | (Bookmark.description.ilike(f"%{search}%"))
        )
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0

    q = q.order_by(Bookmark.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    bookmarks = result.scalars().all()

    data = []
    for bm in bookmarks:
        tags = _parse_tags(bm.tags)
        data.append(_to_out(bm, tags).model_dump())

    return Response.ok(data={"items": data, "total": total, "page": page, "page_size": page_size})


@router.get("/export")
def export_bookmarks(
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.user_id == user.id).order_by(Bookmark.created_at.desc()))
    bookmarks = result.scalars().all()

    data = []
    for bm in bookmarks:
        tags = _parse_tags(bm.tags)
        data.append(_to_out(bm, tags).model_dump(mode='json'))

    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=bookmarks-export-{datetime.now().strftime('%Y-%m-%d')}.json"
        },
    )


@router.post("/import", response_model=Response)
def import_bookmarks(
    browser: str = Form(""),
    file: UploadFile = File(...),
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Only .html/.htm files are accepted").model_dump_json())

    try:
        content = file.file.read().decode('utf-8', errors='replace')
    except Exception:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Cannot read file").model_dump_json())

    imported = import_bookmarks_with_ai(db, content, browser, user.id)
    return Response.ok(data={"count": imported, "browser": browser})


# In-memory progress tracking: {user_id: {total, completed, running, error}}
_analysis_progress: dict[int, dict] = {}
_progress_lock = threading.Lock()


def _run_analysis(user_id: int):
    """Background thread: run AI analysis on all bookmarks missing AI-generated fields."""
    db = SessionLocal()
    try:
        result = db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id,
                Bookmark.generated_title == "",
            )
        )
        candidates = result.scalars().all()

        with _progress_lock:
            _analysis_progress[user_id] = {"total": len(candidates), "completed": 0, "running": True, "error": ""}

        for bm in candidates:
            # Scrape the actual page content with Playwright first
            scraped = scrape_page_sync(bm.url)
            page_title = scraped.get("page_title", "") or getattr(bm, "page_title", "") or ""
            page_description = scraped.get("page_description", "") or getattr(bm, "page_description", "") or ""
            page_text = scraped.get("page_text", "") or getattr(bm, "page_text", "") or ""
            scrape_error = scraped.get("error", "")

            # Store scraped content on the bookmark
            if page_title:
                bm.page_title = page_title
            if page_description:
                bm.page_description = page_description
            if page_text:
                bm.page_text = page_text

            ai = analyze_bookmark(
                url=bm.url,
                bookmark_title=bm.title,
                page_title=page_title,
                page_description=page_description,
                page_text=page_text,
            )

            bm.generated_title = ai.get("generated_title", "")
            bm.generated_description = ai.get("generated_description", "")
            bm.category = ai.get("category", "") or bm.category
            bm.crawl_error = scrape_error or ai.get("crawl_error", "")

            tags_str = ai.get("tags", "")
            if tags_str:
                existing = _parse_tags(bm.tags)
                ai_tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                merged = list(set(existing + ai_tags))
                bm.tags = json.dumps(merged, ensure_ascii=False)

            db.add(AuditLog(user_id=user_id, action="ai_analyze", target_type="bookmark", target_id=bm.id))

            with _progress_lock:
                _analysis_progress[user_id]["completed"] += 1

            db.commit()

        with _progress_lock:
            _analysis_progress[user_id]["running"] = False

    except Exception as e:
        with _progress_lock:
            _analysis_progress[user_id]["running"] = False
            _analysis_progress[user_id]["error"] = str(e)[:500]
    finally:
        db.close()


@router.post("/analyze-all", response_model=Response)
def analyze_all_bookmarks(
    user: User = Depends(get_current_user),
):
    """Start background AI analysis on all bookmarks missing AI-generated fields."""
    with _progress_lock:
        task = _analysis_progress.get(user.id)
        if task and task["running"]:
            return Response.ok(data={"message": "Analysis already in progress", "progress": _progress_snapshot(user.id)})

    thread = threading.Thread(target=_run_analysis, args=(user.id,), daemon=True)
    thread.start()
    return Response.ok(data={"message": "Analysis started", "progress": {"total": 0, "completed": 0, "running": True}})


@router.get("/analyze-progress", response_model=Response)
def get_analysis_progress(
    user: User = Depends(get_current_user),
):
    """Get progress of running analysis task."""
    return Response.ok(data=_progress_snapshot(user.id))


def _progress_snapshot(user_id: int) -> dict:
    p = _analysis_progress.get(user_id, {})
    return {
        "total": p.get("total", 0),
        "completed": p.get("completed", 0),
        "running": p.get("running", False),
        "error": p.get("error", ""),
    }


PUSH_TOKEN_KEY = "push_api_token"


def _get_push_token() -> str:
    """Get or generate the push API token stored in system_config."""
    db = SessionLocal()
    try:
        result = db.execute(select(SystemConfig).where(SystemConfig.key == PUSH_TOKEN_KEY)).scalar_one_or_none()
        if result and result.value:
            return result.value.strip()
        token = secrets.token_urlsafe(32)
        cfg = SystemConfig(key=PUSH_TOKEN_KEY, value=token)
        db.add(cfg)
        db.commit()
        return token
    finally:
        db.close()


def verify_push_token(authorization: str = Header(..., alias="Authorization")) -> str:
    """Validate Bearer token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=403,
            detail=Response.error(ERROR_PERMISSION_DENIED, "Invalid authorization format, expected: Bearer <token>").model_dump_json(),
        )
    token = authorization[7:]
    expected = _get_push_token()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=403,
            detail=Response.error(ERROR_PERMISSION_DENIED, "Invalid push token").model_dump_json(),
        )
    return token


@router.post("/push", response_model=Response)
async def push_bookmarks(
    request: Request,
    db=Depends(get_db),
    token: str = Depends(verify_push_token),
):
    """Receive bookmarks from browser extension. Upsert by URL.
    Supports: {"bookmarks": [...]} or direct single/list of bookmark objects.
    """
    user_id = 1  # Default admin user for browser extension push

    raw = await request.json()

    # Parse: support wrapped {"bookmarks": [...]}, single dict, or list
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and "bookmarks" in raw:
        items = raw["bookmarks"]
    elif isinstance(raw, dict) and "url" in raw:
        items = [raw]
    else:
        raise HTTPException(
            status_code=400,
            detail=Response.error(ERROR_BAD_REQUEST, "Expected list, {bookmarks:[...]}, or bookmark object").model_dump_json(),
        )

    created = 0
    updated = 0

    for item in items:
        url = item.get("url", "").strip()
        if not url:
            continue

        result = db.execute(
            select(Bookmark).where(Bookmark.url == url, Bookmark.user_id == user_id)
        ).scalar_one_or_none()

        is_new = result is None
        if is_new:
            bm = Bookmark(url=url, user_id=user_id)
            db.add(bm)
            created += 1
        else:
            bm = result
            updated += 1

        title = item.get("bookmark_title", "").strip()
        if title:
            bm.title = title
        elif is_new:
            bm.title = url

        for field in ("folder_path", "date_added", "page_title", "page_description",
                       "page_text", "generated_title", "generated_description", "crawl_error"):
            val = item.get(field, "")
            if val:
                setattr(bm, field, val)

        tags_val = item.get("tags", "")
        if tags_val:
            if isinstance(tags_val, str):
                tags_val = [t.strip() for t in tags_val.split(",") if t.strip()]
            bm.tags = json.dumps(tags_val, ensure_ascii=False)

    db.commit()
    return Response.ok(data={"created": created, "updated": updated, "total": created + updated})
@router.get("/push-token", response_model=Response)
def get_push_token():
    """Get the push API token for browser extension."""
    token = _get_push_token()
    return Response.ok(data={"token": token})


@router.post("/push-token/rotate", response_model=Response)
def rotate_push_token():
    """Rotate the push API token."""
    db = SessionLocal()
    try:
        result = db.execute(select(SystemConfig).where(SystemConfig.key == PUSH_TOKEN_KEY)).scalar_one_or_none()
        new_token = secrets.token_urlsafe(32)
        if result:
            result.value = new_token
        else:
            db.add(SystemConfig(key=PUSH_TOKEN_KEY, value=new_token))
        db.commit()
        return Response.ok(data={"token": new_token})
    finally:
        db.close()


@router.post("/batch-delete", response_model=Response)
def batch_delete_bookmarks(
    body: BatchDeleteRequest,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete multiple bookmarks. All must belong to the current user."""
    ids = body.ids
    to_delete = []
    for bid in ids:
        result = db.execute(
            select(Bookmark).where(Bookmark.id == bid, Bookmark.user_id == user.id)
        ).scalar_one_or_none()
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=Response.error(ERROR_NOT_FOUND, f"Bookmark {bid} not found").model_dump_json(),
            )
        to_delete.append(result)

    for bm in to_delete:
        db.delete(bm)
        db.add(AuditLog(user_id=user.id, action="delete", target_type="bookmark", target_id=bm.id))
    db.commit()
    return Response.ok(data={"deleted": len(to_delete)})


@router.get("/{bookmark_id}", response_model=Response)
def get_bookmark(
    bookmark_id: int,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)).scalar_one_or_none()
    bm = result
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())
    tags = _parse_tags(bm.tags)
    return Response.ok(data=_to_out(bm, tags).model_dump())


@router.put("/{bookmark_id}", response_model=Response)
def update_bookmark(
    bookmark_id: int,
    body: BookmarkUpdate,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)).scalar_one_or_none()
    bm = result
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "tags" and value is not None:
            setattr(bm, key, json.dumps(value, ensure_ascii=False))
        else:
            setattr(bm, key, value)

    db.add(AuditLog(user_id=user.id, action="update", target_type="bookmark", target_id=bookmark_id))
    db.commit()
    db.refresh(bm)
    tags = _parse_tags(bm.tags)
    return Response.ok(data=_to_out(bm, tags).model_dump())


@router.delete("/{bookmark_id}", response_model=Response)
def delete_bookmark(
    bookmark_id: int,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)).scalar_one_or_none()
    bm = result
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())

    db.delete(bm)
    db.add(AuditLog(user_id=user.id, action="delete", target_type="bookmark", target_id=bookmark_id))
    db.commit()
    return Response.ok(data={"deleted": bookmark_id})


def _parse_tags(raw) -> list:
    """Safely parse tags from DB or external input. Returns list."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _to_out(bm: Bookmark, tags: list) -> BookmarkOut:
    return BookmarkOut(
        id=bm.id,
        title=bm.title,
        url=bm.url,
        description=bm.description,
        author=bm.author,
        category=bm.category,
        tags=tags,
        rating=bm.rating,
        user_id=bm.user_id,
        created_at=bm.created_at,
        updated_at=bm.updated_at,
        folder_path=getattr(bm, 'folder_path', '') or '',
        date_added=getattr(bm, 'date_added', '') or '',
        page_title=getattr(bm, 'page_title', '') or '',
        page_description=getattr(bm, 'page_description', '') or '',
        page_text=getattr(bm, 'page_text', '') or '',
        generated_title=getattr(bm, 'generated_title', '') or '',
        generated_description=getattr(bm, 'generated_description', '') or '',
        crawl_error=getattr(bm, 'crawl_error', '') or '',
    )
