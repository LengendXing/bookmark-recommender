from pydantic import BaseModel, Field
from typing import Optional


class CollectionCreate(BaseModel):
    name: str = Field(max_length=128)
    description: str = ""


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionOut(BaseModel):
    id: int
    name: str
    description: str
    user_id: int
    bookmark_count: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
