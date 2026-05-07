from typing import Optional

from pydantic import BaseModel, Field


class ApiRouteCreate(BaseModel):
    method: str = Field(..., pattern=r"^(GET|POST|PUT|DELETE|PATCH)$")
    path: str = Field(..., min_length=1, max_length=512)
    summary: str = ""
    tags: list[str] = []
    description: str = ""
    enabled: bool = True


class ApiRouteUpdate(BaseModel):
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ApiRouteOut(BaseModel):
    id: int
    method: str
    path: str
    summary: str
    tags: list[str]
    description: str
    enabled: bool
    source: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, route):
        import json
        tags = []
        try:
            tags = json.loads(route.tags) if route.tags else []
        except (json.JSONDecodeError, TypeError):
            pass
        return cls(
            id=route.id,
            method=route.method,
            path=route.path,
            summary=route.summary or "",
            tags=tags,
            description=route.description or "",
            enabled=bool(route.enabled),
            source=route.source or "auto",
        )
