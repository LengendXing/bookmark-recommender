from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.models.model_version import ModelVersion
from app.models.user import User
from app.schemas import Response, ERROR_NOT_FOUND
from app.schemas.user import VerifyRequest
from app.services.embedding import train_index

router = APIRouter()


@router.get("/audit-logs", response_model=Response)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str = Query("", description="Filter by action"),
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0

    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    logs = result.scalars().all()

    data = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "created_at": log.created_at,
        }
        for log in logs
    ]
    return Response.ok(data={"items": data, "total": total, "page": page, "page_size": page_size})


@router.get("/stats", response_model=Response)
def dashboard_stats(db=Depends(get_db), user: User = Depends(get_admin_user)):
    bm_count = db.execute(select(func.count(Bookmark.id))).scalar() or 0
    user_count = db.execute(select(func.count(User.id))).scalar() or 0
    log_count = db.execute(select(func.count(AuditLog.id))).scalar() or 0
    latest_model = db.execute(select(ModelVersion).order_by(ModelVersion.created_at.desc()).limit(1))
    latest_model = latest_model.scalar_one_or_none()

    return Response.ok(data={
        "bookmarks": bm_count,
        "users": user_count,
        "audit_logs": log_count,
        "latest_model": {
            "version": latest_model.version,
            "status": latest_model.status,
            "created_at": latest_model.created_at,
        } if latest_model else None,
    })


@router.post("/train", response_model=Response)
def trigger_train(
    body: VerifyRequest,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    try:
        train_index()
        return Response.ok(data={"status": "trained"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=Response.error(5000, str(e)).model_dump_json())


@router.delete("/bookmark/{bookmark_id}", response_model=Response)
def admin_delete_bookmark(
    bookmark_id: int,
    body: VerifyRequest,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bm = result.scalar_one_or_none()
    if bm is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Not found").model_dump_json())
    db.delete(bm)
    db.add(AuditLog(user_id=user.id, action="admin_delete", target_type="bookmark", target_id=bookmark_id))
    db.commit()
    return Response.ok(data={"deleted": bookmark_id})


@router.post("/user/{user_id}/kick", response_model=Response)
def kick_user(
    user_id: int,
    body: VerifyRequest,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Not found").model_dump_json())
    target.is_active = False
    db.add(AuditLog(user_id=user.id, action="kick", target_type="user", target_id=user_id))
    db.commit()
    return Response.ok(data={"kicked": user_id})
