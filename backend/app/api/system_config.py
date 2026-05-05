import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST

router = APIRouter()

ALLOWED_KEYS = {"api_endpoint", "api_key"}


def _mask_key(value: str) -> str:
    if len(value) > 4:
        return "***" + value[-4:]
    return "***"


@router.get("", response_model=Response)
def get_configs(
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(select(SystemConfig))
    configs = result.scalars().all()
    data = {}
    for cfg in configs:
        if cfg.key == "api_key":
            data[cfg.key] = _mask_key(cfg.value) if cfg.value else ""
        else:
            data[cfg.key] = cfg.value
    return Response.ok(data=data)


@router.put("", response_model=Response)
def update_configs(
    body: dict,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    for key, value in body.items():
        if key not in ALLOWED_KEYS:
            raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, f"Invalid config key: {key}").model_dump_json())

        result = db.execute(select(SystemConfig).where(SystemConfig.key == key)).scalar_one_or_none()
        if result:
            result.value = value
        else:
            db.add(SystemConfig(key=key, value=value))

    db.add(AuditLog(user_id=user.id, action="update_config", target_type="system", target_id=0))
    db.commit()
    return Response.ok(data={"updated": list(body.keys())})
