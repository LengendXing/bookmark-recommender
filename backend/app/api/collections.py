from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.bookmark import Bookmark
from app.models.collection import Collection
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND
from app.schemas.collection import CollectionCreate, CollectionOut, CollectionUpdate

router = APIRouter()


@router.get("", response_model=Response)
def list_collections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(
        select(Collection).where(Collection.user_id == user.id).order_by(Collection.created_at.desc())
    )
    collections = result.scalars().all()

    data = []
    for c in collections:
        count = db.execute(
            select(func.count()).select_from(Bookmark).where(
                Bookmark.collection_id == c.id  # type: ignore
            )
        ).scalar() or 0
        data.append(CollectionOut(
            id=c.id,
            name=c.name,
            description=c.description,
            user_id=c.user_id,
            bookmark_count=count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ).model_dump())

    return Response.ok(data=data)


@router.post("", response_model=Response)
def create_collection(
    body: CollectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = Collection(name=body.name, description=body.description, user_id=user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return Response.ok(data=CollectionOut(
        id=c.id, name=c.name, description=c.description, user_id=c.user_id,
        bookmark_count=0, created_at=c.created_at, updated_at=c.updated_at,
    ).model_dump())


@router.put("/{collection_id}", response_model=Response)
def update_collection(
    collection_id: int,
    body: CollectionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.user_id == user.id)
    ).scalar_one_or_none()
    c = result
    if c is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Collection not found").model_dump_json())

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(c, key, value)

    db.commit()
    db.refresh(c)

    count = db.execute(
        select(func.count()).select_from(Bookmark).where(Bookmark.collection_id == c.id)  # type: ignore
    ).scalar() or 0

    return Response.ok(data=CollectionOut(
        id=c.id, name=c.name, description=c.description, user_id=c.user_id,
        bookmark_count=count, created_at=c.created_at, updated_at=c.updated_at,
    ).model_dump())


@router.delete("/{collection_id}", response_model=Response)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.user_id == user.id)
    ).scalar_one_or_none()
    c = result
    if c is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Collection not found").model_dump_json())

    from sqlalchemy import update
    db.execute(update(Bookmark).where(Bookmark.collection_id == collection_id).values(collection_id=None))  # type: ignore
    db.delete(c)
    db.commit()
    return Response.ok(data={"deleted": collection_id})
