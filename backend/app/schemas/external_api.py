from typing import Optional

from pydantic import BaseModel, Field


class HeaderParam(BaseModel):
    key: str
    value: str = ""
    required: bool = False


class QueryParam(BaseModel):
    key: str
    type: str = "string"
    required: bool = False


class ExternalApiCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    method: str = Field(..., pattern=r"^(GET|POST|PUT|DELETE|PATCH)$")
    path: str = Field(..., min_length=1, max_length=512)
    description: str = ""
    headers: list[HeaderParam] = []
    params: list[QueryParam] = []
    script: str = ""
    enabled: bool = True
    is_native: bool = False


class ExternalApiUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    headers: Optional[list[HeaderParam]] = None
    params: Optional[list[QueryParam]] = None
    script: Optional[str] = None
    enabled: Optional[bool] = None


class ExternalApiOut(BaseModel):
    id: int
    name: str
    method: str
    path: str
    description: str
    headers: list[dict]
    params: list[dict]
    script: str
    enabled: bool
    is_native: bool
    created_at: str = ""
    updated_at: str = ""

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, api):
        import json

        def _parse_json(raw, default):
            try:
                return json.loads(raw) if raw else default
            except (json.JSONDecodeError, TypeError):
                return default

        return cls(
            id=api.id,
            name=api.name,
            method=api.method,
            path=api.path,
            description=api.description or "",
            headers=_parse_json(api.headers, []),
            params=_parse_json(api.params, []),
            script=api.script or "",
            enabled=bool(api.enabled),
            is_native=bool(api.is_native),
            created_at=getattr(api, "created_at", "") or "",
            updated_at=getattr(api, "updated_at", "") or "",
        )
