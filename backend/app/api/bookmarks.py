import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.collection import Collection
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND
from app.schemas.bookmark import BookmarkCreate, BookmarkMove, BookmarkOut, BookmarkUpdate
from app.services.ingest import ingest_bulk, ingest_single
from app.services.import_service import import_bookmarks_with_ai

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
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else bm.tags
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
        tags = json.loads(bm.tags) if isinstance(bm.tags, str) else bm.tags
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
    collection_id: int | None = Query(None, description="Filter by collection"),
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Bookmark).where(Bookmark.user_id == user.id)
    if search:
        q = q.where(
            (Bookmark.title.ilike(f"%{search}%")) | (Bookmark.description.ilike(f"%{search}%"))
        )
    if collection_id is not None:
        q = q.where(Bookmark.collection_id == collection_id)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0

    q = q.order_by(Bookmark.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    bookmarks = result.scalars().all()

    data = []
    for bm in bookmarks:
        tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
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
        tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
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
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
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
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
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


@router.post("/{bookmark_id}/move", response_model=Response)
def move_bookmark(
    bookmark_id: int,
    body: BookmarkMove,
    db = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)).scalar_one_or_none()
    bm = result
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())

    if body.collection_id is not None:
        col = db.execute(select(Collection).where(Collection.id == body.collection_id, Collection.user_id == user.id)).scalar_one_or_none()
        if col is None:
            raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Collection not found").model_dump_json())

    bm.collection_id = body.collection_id
    db.commit()
    db.refresh(bm)
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
    return Response.ok(data=_to_out(bm, tags).model_dump())


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
        collection_id=getattr(bm, 'collection_id', None),
    )
