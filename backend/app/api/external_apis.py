import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, delete as sa_delete

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.external_api import ExternalApi
from app.models.api_call_log import ApiCallLog
from app.models.user import User
from app.schemas import Response
from app.schemas.external_api import ExternalApiCreate, ExternalApiOut, ExternalApiUpdate
from app.services.script_executor import execute_script

logger = logging.getLogger(__name__)

router = APIRouter()


def _ext_api_out(api: ExternalApi) -> dict:
    return ExternalApiOut.from_orm_obj(api).model_dump()


# ---------------------------------------------------------------------------
# Dynamic route handler builder
# ---------------------------------------------------------------------------

def _build_route_handler(api: ExternalApi):
    """Build a FastAPI endpoint handler for an external API record."""
    from app.core.database import SessionLocal

    async def handler(request: Request):
        start = time.time()

        # Parse request body
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass

        client_ip = request.client.host if request.client else "unknown"

        # Build headers dict
        headers_in = dict(request.headers)

        # Build query params
        params_in = dict(request.query_params)

        # Execute script
        result = execute_script(api.script, body, headers_in, params_in)

        duration_ms = (time.time() - start) * 1000
        status = result.get("status", 200)
        error_msg = result.get("error", "")

        # Fire-and-forget log write
        try:
            db = SessionLocal()
            log_entry = ApiCallLog(
                api_id=api.id,
                method=api.method,
                path=api.path,
                request_body=json.dumps(body, ensure_ascii=False)[:4096],
                response_status=status,
                response_body=json.dumps(result, ensure_ascii=False)[:4096],
                duration_ms=round(duration_ms, 2),
                error=error_msg[:1024] if error_msg else "",
                client_ip=client_ip,
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"Failed to write API call log: {e}")

        if not result.get("ok"):
            raise HTTPException(status_code=status, detail=error_msg or "Script execution failed")

        return result.get("data", result)

    return handler


# ---------------------------------------------------------------------------
# Route registration / unregistration
# ---------------------------------------------------------------------------

def _register_route(app, api: ExternalApi):
    """Register an external API as a live FastAPI route."""
    route_handler = _build_route_handler(api)
    app.add_api_route(
        api.path,
        route_handler,
        methods=[api.method],
        tags=["external"],
        name=f"ext_{api.id}",
    )


def _unregister_route(app, api: ExternalApi):
    """Remove a previously registered external API route."""
    app.router.routes = [
        r for r in app.routes
        if not (hasattr(r, "name") and r.name == f"ext_{api.id}")
    ]


def register_all_external_routes(app):
    """Register all enabled external APIs at startup."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        apis = db.execute(
            select(ExternalApi).where(ExternalApi.enabled == True)
        ).scalars().all()
        for api in apis:
            if api.script or api.is_native:
                try:
                    _register_route(app, api)
                    logger.info(f"[INIT] Registered external route: {api.method} {api.path}")
                except Exception as e:
                    logger.error(f"[INIT] Failed to register {api.method} {api.path}: {e}")
    finally:
        db.close()


def seed_native_endpoints(app):
    """Discover native endpoints (e.g. push) and create ExternalApi records."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        existing_count = db.execute(
            select(func.count()).select_from(ExternalApi)
        ).scalar() or 0

        if existing_count == 0:
            db.add(ExternalApi(
                name="书签推送",
                method="POST",
                path="/api/bookmarks/push",
                description="浏览器插件推送书签（原生内置端点，支持 3 种数据格式：数组 / {bookmarks:[...]} / 单个对象）",
                script="",
                is_native=True,
                enabled=True,
            ))
            db.commit()
            logger.info("[INIT] Seeded native push endpoint to external_apis.")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Admin CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=Response)
def list_external_apis(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    method: str = Query(""),
    search: str = Query(""),
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    q = select(ExternalApi)
    if method:
        q = q.where(ExternalApi.method == method.upper())
    if search:
        q = q.where(
            (ExternalApi.path.contains(search)) | (ExternalApi.name.contains(search))
        )

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    q = q.order_by(ExternalApi.path, ExternalApi.method).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(q)
    apis = result.scalars().all()

    return Response.ok(data={
        "items": [_ext_api_out(a) for a in apis],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{api_id}", response_model=Response)
def get_external_api(
    api_id: int,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ExternalApi).where(ExternalApi.id == api_id))
    api = result.scalar_one_or_none()
    if api is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "External API not found").model_dump_json())
    return Response.ok(data=_ext_api_out(api))


@router.post("", response_model=Response)
def create_external_api(
    body: ExternalApiCreate,
    request: Request,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    existing = db.execute(
        select(ExternalApi).where(ExternalApi.method == body.method, ExternalApi.path == body.path)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=Response.error(2001, f"API {body.method} {body.path} already exists").model_dump_json(),
        )

    api = ExternalApi(
        name=body.name,
        method=body.method,
        path=body.path,
        description=body.description,
        headers=json.dumps([h.model_dump() for h in body.headers], ensure_ascii=False),
        params=json.dumps([p.model_dump() for p in body.params], ensure_ascii=False),
        script=body.script,
        enabled=body.enabled,
        is_native=body.is_native,
    )
    db.add(api)
    db.commit()
    db.refresh(api)

    if api.enabled and api.script:
        try:
            _register_route(request.app, api)
            logger.info(f"Registered external route: {api.method} {api.path}")
        except Exception as e:
            logger.error(f"Failed to register route {api.method} {api.path}: {e}")

    return Response.ok(data=_ext_api_out(api))


@router.put("/{api_id}", response_model=Response)
def update_external_api(
    api_id: int,
    body: ExternalApiUpdate,
    request: Request,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ExternalApi).where(ExternalApi.id == api_id))
    api = result.scalar_one_or_none()
    if api is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "External API not found").model_dump_json())

    if api.is_native:
        # Only allow toggling enabled/description for native endpoints
        if body.description is not None:
            api.description = body.description
        if body.enabled is not None:
            api.enabled = body.enabled
    else:
        if body.name is not None:
            api.name = body.name
        if body.description is not None:
            api.description = body.description
        if body.headers is not None:
            api.headers = json.dumps([h.model_dump() for h in body.headers], ensure_ascii=False)
        if body.params is not None:
            api.params = json.dumps([p.model_dump() for p in body.params], ensure_ascii=False)
        if body.script is not None:
            api.script = body.script
        if body.enabled is not None:
            api.enabled = body.enabled

    db.add(api)
    db.commit()
    db.refresh(api)

    _unregister_route(request.app, api)
    if api.enabled and api.script:
        try:
            _register_route(request.app, api)
        except Exception as e:
            logger.error(f"Failed to re-register route {api.method} {api.path}: {e}")

    return Response.ok(data=_ext_api_out(api))


@router.delete("/{api_id}", response_model=Response)
def delete_external_api(
    api_id: int,
    request: Request,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ExternalApi).where(ExternalApi.id == api_id))
    api = result.scalar_one_or_none()
    if api is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "External API not found").model_dump_json())
    if api.is_native:
        raise HTTPException(status_code=400, detail=Response.error(2003, "Native endpoints cannot be deleted").model_dump_json())

    _unregister_route(request.app, api)
    db.delete(api)
    db.commit()
    return Response.ok(data={"deleted": api_id})


@router.post("/{api_id}/test", response_model=Response)
def test_external_api(
    api_id: int,
    body: dict,
    db=Depends(get_db),
    user: User = Depends(get_admin_user),
):
    result = db.execute(select(ExternalApi).where(ExternalApi.id == api_id))
    api = result.scalar_one_or_none()
    if api is None:
        raise HTTPException(status_code=404, detail=Response.error(2002, "External API not found").model_dump_json())
    if not api.script:
        raise HTTPException(status_code=400, detail=Response.error(2003, "API has no script to test").model_dump_json())

    test_data = body.get("data", {})
    test_headers = body.get("headers", {})
    test_params = body.get("params", {})

    start = time.time()
    result = execute_script(api.script, test_data, test_headers, test_params)
    duration_ms = (time.time() - start) * 1000

    return Response.ok(data={
        "result": result,
        "duration_ms": round(duration_ms, 2),
    })
