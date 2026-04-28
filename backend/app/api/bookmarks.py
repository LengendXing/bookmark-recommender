import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND
from app.schemas.bookmark import BookmarkCreate, BookmarkOut, BookmarkUpdate
from app.services.ingest import ingest_bulk, ingest_single

router = APIRouter()


@router.post("/ingest", response_model=Response)
async def ingest(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "URL required").model_dump_json())

    bm = await ingest_single(db, url, user.id)
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else bm.tags
    return Response.ok(data=_to_out(bm, tags).model_dump())


@router.post("/ingest-bulk", response_model=Response)
async def ingest_bulk_endpoint(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    urls = body.get("urls", [])
    if not urls:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "urls array required").model_dump_json())

    bookmarks = await ingest_bulk(db, urls, user.id)
    data = []
    for bm in bookmarks:
        tags = json.loads(bm.tags) if isinstance(bm.tags, str) else bm.tags
        data.append(_to_out(bm, tags).model_dump())
    return Response.ok(data=data)


@router.post("", response_model=Response)
async def create_bookmark(
    body: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
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
    await db.commit()
    await db.refresh(bm)
    return Response.ok(data=_to_out(bm, body.tags).model_dump())


@router.get("", response_model=Response)
async def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Search title/description"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Bookmark).where(Bookmark.user_id == user.id)
    if search:
        q = q.where(
            (Bookmark.title.ilike(f"%{search}%")) | (Bookmark.description.ilike(f"%{search}%"))
        )
    total = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total.scalar() or 0

    q = q.order_by(Bookmark.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    bookmarks = result.scalars().all()

    data = []
    for bm in bookmarks:
        tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
        data.append(_to_out(bm, tags).model_dump())

    return Response.ok(data={"items": data, "total": total, "page": page, "page_size": page_size})


@router.get("/{bookmark_id}", response_model=Response)
async def get_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id))
    bm = result.scalar_one_or_none()
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
    return Response.ok(data=_to_out(bm, tags).model_dump())


@router.put("/{bookmark_id}", response_model=Response)
async def update_bookmark(
    bookmark_id: int,
    body: BookmarkUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id))
    bm = result.scalar_one_or_none()
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "tags" and value is not None:
            setattr(bm, key, json.dumps(value, ensure_ascii=False))
        else:
            setattr(bm, key, value)

    db.add(AuditLog(user_id=user.id, action="update", target_type="bookmark", target_id=bookmark_id))
    await db.commit()
    await db.refresh(bm)
    tags = json.loads(bm.tags) if isinstance(bm.tags, str) else []
    return Response.ok(data=_to_out(bm, tags).model_dump())


@router.delete("/{bookmark_id}", response_model=Response)
async def delete_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id))
    bm = result.scalar_one_or_none()
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Bookmark not found").model_dump_json())

    db.delete(bm)
    db.add(AuditLog(user_id=user.id, action="delete", target_type="bookmark", target_id=bookmark_id))
    await db.commit()
    return Response.ok(data={"deleted": bookmark_id})


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
    )
