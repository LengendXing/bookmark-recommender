import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.api_route import ApiRoute
from app.models.external_api import ExternalApi
from app.models.api_call_log import ApiCallLog
from app.models.user import User
from app.schemas import Response
from app.schemas.api_call_log import ApiCallLogOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api-stats", response_model=Response)
def get_stats(
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    internal_count = db.execute(select(func.count()).select_from(ApiRoute)).scalar() or 0
    external_count = db.execute(select(func.count()).select_from(ExternalApi)).scalar() or 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    calls_today = db.execute(
        select(func.count()).select_from(ApiCallLog).where(ApiCallLog.created_at >= today)
    ).scalar() or 0

    return Response.ok(data={
        "internal_count": internal_count,
        "external_count": external_count,
        "calls_today": calls_today,
    })


@router.get("/api-call-logs", response_model=Response)
def list_call_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    api_id: int = Query(None),
    method: str = Query(""),
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    q = select(ApiCallLog)
    if api_id:
        q = q.where(ApiCallLog.api_id == api_id)
    if method:
        q = q.where(ApiCallLog.method == method.upper())

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    q = q.order_by(ApiCallLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append(ApiCallLogOut.model_validate(log).model_dump())

    return Response.ok(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/api-call-logs/{log_id}", response_model=Response)
def get_call_log_detail(
    log_id: int,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ApiCallLog).where(ApiCallLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "Call log not found").model_dump_json())
    return Response.ok(data=ApiCallLogOut.model_validate(log).model_dump())
