import json
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas import Response, ERROR_BAD_REQUEST

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_KEYS = {"api_endpoint", "api_key", "api_provider", "ai_model"}


class ModelTestRequest(BaseModel):
    api_endpoint: str
    api_key: str
    api_provider: str = "openai"
    model: str


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


@router.post("/test", response_model=Response)
def test_model(body: ModelTestRequest, user: User = Depends(get_current_user)):
    endpoint = body.api_endpoint.rstrip("/")
    messages = [{"role": "user", "content": "Hello, respond with just the word 'OK'."}]

    try:
        if body.api_provider == "anthropic":
            url = f"{endpoint}/messages"
            headers = {
                "x-api-key": body.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": body.model,
                "max_tokens": 50,
                "messages": messages,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=Response.error(
                        ERROR_BAD_REQUEST,
                        f"API error ({resp.status_code}): {resp.text[:500]}"
                    ).model_dump_json())
                data = resp.json()
                content = "".join(block.get("text", "") for block in data.get("content", []))
                usage = data.get("usage", {})
        else:
            url = f"{endpoint}/chat/completions"
            headers = {
                "Authorization": f"Bearer {body.api_key}",
                "content-type": "application/json",
            }
            payload = {
                "model": body.model,
                "max_tokens": 50,
                "messages": messages,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=Response.error(
                        ERROR_BAD_REQUEST,
                        f"API error ({resp.status_code}): {resp.text[:500]}"
                    ).model_dump_json())
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

        return Response.ok(data={
            "success": True,
            "response": content,
            "model": data.get("model", body.model),
            "tokens": usage,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model test failed: {e}")
        raise HTTPException(status_code=400, detail=Response.error(
            ERROR_BAD_REQUEST, f"Connection failed: {str(e)}"
        ).model_dump_json())


@router.post("/models", response_model=Response)
def list_models(body: ModelTestRequest, user: User = Depends(get_current_user)):
    endpoint = body.api_endpoint.rstrip("/")

    if body.api_provider == "anthropic":
        preset = [
            "claude-opus-4-7-20250601",
            "claude-sonnet-4-6-20250514",
            "claude-haiku-4-5-20251001",
        ]
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{endpoint}/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    if models:
                        return Response.ok(data={"models": models})
        except Exception:
            pass
        return Response.ok(data={"models": preset})
    else:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{endpoint}/models",
                    headers={"Authorization": f"Bearer {body.api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return Response.ok(data={"models": models})
        except Exception:
            pass
        return Response.ok(data={"models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]})
