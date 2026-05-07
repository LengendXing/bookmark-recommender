import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, delete as sa_delete

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.api_route import ApiRoute
from app.models.user import User
from app.schemas import Response
from app.schemas.api_route import ApiRouteCreate, ApiRouteOut, ApiRouteUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


def _route_out(route: ApiRoute) -> dict:
    tags = []
    try:
        tags = json.loads(route.tags) if route.tags else []
    except (json.JSONDecodeError, TypeError):
        pass
    return {
        "id": route.id,
        "method": route.method,
        "path": route.path,
        "summary": route.summary or "",
        "tags": tags,
        "description": route.description or "",
        "enabled": bool(route.enabled),
        "source": route.source or "auto",
    }


@router.get("", response_model=Response)
def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    method: str = Query(""),
    tag: str = Query(""),
    search: str = Query(""),
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    q = select(ApiRoute)
    if method:
        q = q.where(ApiRoute.method == method.upper())
    if tag:
        q = q.where(ApiRoute.tags.contains(f'"{tag}"'))
    if search:
        q = q.where(
            (ApiRoute.path.contains(search)) | (ApiRoute.summary.contains(search))
        )

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    q = q.order_by(ApiRoute.path, ApiRoute.method).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    routes = result.scalars().all()

    return Response.ok(data={
        "items": [_route_out(r) for r in routes],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/stats", response_model=Response)
def get_stats(
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    from datetime import datetime, timezone

    internal_count = db.execute(select(func.count()).select_from(ApiRoute)).scalar() or 0

    q_ext = select(func.count())
    try:
        from app.models.external_api import ExternalApi
        q_ext = q_ext.select_from(ExternalApi)
    except Exception:
        pass
    external_count = db.execute(q_ext).scalar() or 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    calls_today = 0
    recent_calls = []
    try:
        from app.models.api_call_log import ApiCallLog
        calls_today = db.execute(
            select(func.count()).select_from(ApiCallLog).where(ApiCallLog.created_at >= today)
        ).scalar() or 0

        recent = db.execute(
            select(ApiCallLog).order_by(ApiCallLog.created_at.desc()).limit(20)
        ).scalars().all()
        recent_calls = [
            {
                "id": l.id,
                "api_id": l.api_id,
                "method": l.method,
                "path": l.path,
                "request_body": l.request_body or "",
                "response_status": l.response_status,
                "response_body": l.response_body or "",
                "duration_ms": l.duration_ms,
                "error": l.error or "",
                "user_id": l.user_id,
                "client_ip": l.client_ip or "",
                "created_at": l.created_at if l.created_at else "",
            }
            for l in recent
        ]
    except Exception:
        pass

    return Response.ok(data={
        "internal_count": internal_count,
        "external_count": external_count,
        "calls_today": calls_today,
        "recent_calls": recent_calls,
    })


@router.get("/{route_id}", response_model=Response)
def get_route(
    route_id: int,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ApiRoute).where(ApiRoute.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "Route not found").model_dump_json())
    return Response.ok(data=_route_out(route))


@router.post("", response_model=Response)
def create_route(
    body: ApiRouteCreate,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    existing = db.execute(
        select(ApiRoute).where(ApiRoute.method == body.method, ApiRoute.path == body.path)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=Response.error(2001, f"Route {body.method} {body.path} already exists").model_dump_json(),
        )

    route = ApiRoute(
        method=body.method,
        path=body.path,
        summary=body.summary,
        tags=json.dumps(body.tags, ensure_ascii=False),
        description=body.description,
        enabled=body.enabled,
        source="manual",
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return Response.ok(data=_route_out(route))


@router.put("/{route_id}", response_model=Response)
def update_route(
    route_id: int,
    body: ApiRouteUpdate,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ApiRoute).where(ApiRoute.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "Route not found").model_dump_json())

    if body.summary is not None:
        route.summary = body.summary
    if body.tags is not None:
        route.tags = json.dumps(body.tags, ensure_ascii=False)
    if body.description is not None:
        route.description = body.description
    if body.enabled is not None:
        route.enabled = body.enabled

    db.add(route)
    db.commit()
    db.refresh(route)
    return Response.ok(data=_route_out(route))


@router.delete("/{route_id}", response_model=Response)
def delete_route(
    route_id: int,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ApiRoute).where(ApiRoute.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "Route not found").model_dump_json())
    db.delete(route)
    db.commit()
    return Response.ok(data={"deleted": route_id})


@router.post("/sync", response_model=Response)
def sync_routes(
    request: Request,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    """Sync FastAPI registered routes into database. Manual routes are preserved."""
    skip_prefixes = ("/openapi", "/docs", "/redoc")
    skip_paths = ("/health",)
    synced = 0

    for route in request.app.routes:
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
                    method=method,
                    path=path,
                    summary=summary,
                    tags=tags_json,
                    source="auto",
                ))
            synced += 1

    db.commit()
    return Response.ok(data={"synced": synced})
