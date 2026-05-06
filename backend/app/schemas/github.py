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
    user_id: int | None = None
    account_id: int | None
    repo_full_name: str
    repo_name: str
    owner: str
    description: str = ""
    language: str = ""
    language_color: str = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    size_kb: int = 0
    topics: str = ""
    homepage: str = ""
    license: str = ""
    default_branch: str = ""
    archived: bool = False
    readme_text: str = ""
    repo_created_at: str | None = None
    repo_updated_at: str | None = None
    ai_tags: str = ""
    ai_summary: str = ""
    ai_category: str = ""
    ai_analyzed_at: str | None = None
    analyze_error: str = ""
    created_at: str = ""
    updated_at: str = ""

    model_config = {"from_attributes": True}


class RecommendedRepoOut(BaseModel):
    id: int
    user_id: int | None = None
    repo_full_name: str
    repo_name: str
    owner: str
    html_url: str = ""
    clone_url: str = ""
    description: str = ""
    ai_summary: str = ""
    topics: str = ""
    ai_tags: str = ""
    language: str = ""
    language_color: str = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    license: str = ""
    homepage: str = ""
    default_branch: str = ""
    size_kb: int = 0
    archived: bool = False
    score: float = 0.0
    recommend_reason: str = ""
    match_tags: str = ""
    source_tag: str = ""
    is_read: bool = False
    is_starred: bool = False
    recommended_at: str | None = None
    created_at: str = ""
    updated_at: str = ""

    model_config = {"from_attributes": True}


class GitHubImportRequest(BaseModel):
    account_id: int


class GitHubExportData(BaseModel):
    repos: list[dict]


class RepoRecommendationGenerateRequest(BaseModel):
    top_k_tags: int = Field(default=3, ge=1, le=5,
                            description="API 限流策略: GitHub Search API 限制 30 req/min，认证用户 10 req/min 未认证。"
                                        "收窄为 3-5 个高频标签可避免触发限流。后续如需搜索更多标签可调整此值，"
                                        "或改为按标签串行 + sleep 2-3s 方式。")
