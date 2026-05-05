from pydantic import BaseModel, Field
from typing import Optional


class BookmarkIngest(BaseModel):
    url: str = Field(max_length=2048)


class BookmarkCreate(BaseModel):
    title: str = Field(max_length=512)
    url: str = Field(max_length=2048)
    description: str = ""
    author: str = ""
    category: str = ""
    tags: list[str] = []


class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    rating: Optional[int] = Field(None, ge=0, le=5)


class BookmarkOut(BaseModel):
    id: int
    title: str
    url: str
    description: str
    author: str
    category: str
    tags: list[str]
    rating: int
    user_id: int
    created_at: str
    updated_at: str
    folder_path: str = ""
    date_added: str = ""
    page_title: str = ""
    page_description: str = ""
    page_text: str = ""
    generated_title: str = ""
    generated_description: str = ""
    crawl_error: str = ""
    collection_id: int | None = None

    model_config = {"from_attributes": True}


class BookmarkMove(BaseModel):
    collection_id: int | None = None


class RecommendRequest(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    limit: int = Field(default=10, ge=1, le=50)


class RecommendResult(BaseModel):
    id: int
    title: str
    url: str
    description: str = ""
    category: str = ""
    score: float
    tags: list[str]

    model_config = {"from_attributes": True}
