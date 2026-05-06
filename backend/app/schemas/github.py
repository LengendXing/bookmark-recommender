from pydantic import BaseModel, Field
from typing import Optional


class GitHubAccountCreate(BaseModel):
    token: str


class GitHubAccountOut(BaseModel):
    id: int
    user_id: int
    github_login: str
    avatar_url: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class StarredRepoOut(BaseModel):
    id: int
    user_id: int
    account_id: int | None
    repo_full_name: str
    repo_name: str
    owner: str
    description: str
    language: str
    stars: int
    forks: int
    repo_created_at: str | None
    repo_updated_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class GitHubImportRequest(BaseModel):
    account_id: int

class GitHubExportData(BaseModel):
    repos: list[dict]
