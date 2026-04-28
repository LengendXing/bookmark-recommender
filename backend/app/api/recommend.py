from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.model_version import ModelVersion
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_INTERNAL
from app.schemas.bookmark import RecommendRequest, RecommendResult
from app.services.embedding import recommend as recommend_embeddings, train_index

router = APIRouter()


@router.post("", response_model=Response)
async def recommend(
    body: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        results = await recommend_embeddings(body.query, body.limit)
        db.add(AuditLog(user_id=user.id, action="recommend", details=f"query={body.query}"))
        await db.commit()
        return Response.ok(data=[RecommendResult(**r).model_dump() for r in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=Response.error(ERROR_INTERNAL, str(e)).model_dump_json())


@router.post("/train", response_model=Response)
async def trigger_train(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        await train_index()
        db.add(AuditLog(user_id=user.id, action="train", target_type="model"))
        await db.commit()
        return Response.ok(data={"status": "trained"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=Response.error(ERROR_INTERNAL, str(e)).model_dump_json())


@router.get("/model-status", response_model=Response)
async def model_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion)
        .order_by(ModelVersion.created_at.desc())
        .limit(5)
    )
    versions = result.scalars().all()
    data = [
        {
            "id": v.id,
            "model_name": v.model_name,
            "version": v.version,
            "status": v.status,
            "dataset_size": v.dataset_size,
            "created_at": v.created_at,
        }
        for v in versions
    ]
    return Response.ok(data=data)
