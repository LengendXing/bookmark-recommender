import json
import logging
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.github_account import GitHubAccount
from app.models.starred_repo import StarredRepo
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND
from app.schemas.github import GitHubAccountCreate, GitHubAccountOut, GitHubImportRequest, StarredRepoOut
from app.services.github_service import get_user_info, list_starred_repos, GitHubServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Accounts ──────────────────────────────────────────────────────────────────

@router.get("/accounts", response_model=Response)
def list_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(
        select(GitHubAccount).where(
            GitHubAccount.user_id == user.id,
            GitHubAccount.is_deleted == False,
        ).order_by(GitHubAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    data = [GitHubAccountOut.model_validate(a).model_dump() for a in accounts]
    return Response.ok(data=data)


@router.post("/accounts", response_model=Response)
def add_account(
    body: GitHubAccountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Token is required").model_dump_json())

    try:
        info = get_user_info(token)
    except GitHubServiceError as e:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, str(e)).model_dump_json())

    existing = db.execute(
        select(GitHubAccount).where(
            GitHubAccount.user_id == user.id,
            GitHubAccount.github_login == info["github_login"],
        )
    ).scalar_one_or_none()
    if existing:
        existing.token = token
        existing.avatar_url = info["avatar_url"]
        existing.is_deleted = False
        db.commit()
        db.refresh(existing)
        return Response.ok(data=GitHubAccountOut.model_validate(existing).model_dump())

    account = GitHubAccount(
        user_id=user.id,
        github_login=info["github_login"],
        avatar_url=info["avatar_url"],
        token=token,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return Response.ok(data=GitHubAccountOut.model_validate(account).model_dump())


@router.delete("/accounts/{account_id}", response_model=Response)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = db.execute(
        select(GitHubAccount).where(GitHubAccount.id == account_id, GitHubAccount.user_id == user.id, GitHubAccount.is_deleted == False)
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Account not found").model_dump_json())

    account.is_deleted = True
    db.commit()
    return Response.ok(data={"deleted": account_id})


@router.post("/accounts/{account_id}/sync", response_model=Response)
def sync_account(
    account_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = db.execute(
        select(GitHubAccount).where(GitHubAccount.id == account_id, GitHubAccount.user_id == user.id)
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Account not found").model_dump_json())

    imported = 0
    page = 1
    try:
        while True:
            repos, next_link = list_starred_repos(account.token, page=page)
            for r in repos:
                exists = db.execute(
                    select(StarredRepo).where(
                        StarredRepo.user_id == user.id,
                        StarredRepo.repo_full_name == r["repo_full_name"],
                    )
                ).scalar_one_or_none()
                if not exists:
                    db.add(StarredRepo(user_id=user.id, account_id=account.id, **r))
                    imported += 1
            db.commit()
            if not next_link:
                break
            page += 1
    except GitHubServiceError as e:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, str(e)).model_dump_json())

    return Response.ok(data={"imported": imported, "message": f"Synced {imported} new repos"})


# ── Repos ─────────────────────────────────────────────────────────────────────

@router.get("/repos", response_model=Response)
def list_repos(
    q: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(StarredRepo).where(StarredRepo.user_id == user.id)

    if q:
        like = f"%{q}%"
        base = base.where(
            or_(
                StarredRepo.repo_name.ilike(like),
                StarredRepo.owner.ilike(like),
                StarredRepo.description.ilike(like),
                StarredRepo.language.ilike(like),
                StarredRepo.repo_full_name.ilike(like),
            )
        )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = db.execute(count_stmt).scalar() or 0

    offset = (page - 1) * page_size
    result = db.execute(
        base.order_by(StarredRepo.stars.desc().nullslast(), StarredRepo.created_at.desc())
        .offset(offset).limit(page_size)
    )
    repos = result.scalars().all()

    data = [StarredRepoOut.model_validate(r).model_dump() for r in repos]
    return Response.ok(data={"items": data, "total": total, "page": page, "page_size": page_size})


@router.post("/repos/semantic-search", response_model=Response)
def semantic_search_repos(
    query: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Semantic search repos using embedding similarity."""
    if not query or not query.strip():
        return Response.ok(data={"items": [], "total": 0})

    from app.services.embedding import semantic_search

    result = db.execute(select(StarredRepo).where(StarredRepo.user_id == user.id))
    repos = result.scalars().all()

    if not repos:
        return Response.ok(data={"items": [], "total": 0})

    texts = [f"{r.repo_full_name} {r.description} {r.language}" for r in repos]
    indices, scores = semantic_search(query.strip(), texts)

    items = []
    for idx, score in zip(indices, scores):
        r = repos[idx]
        d = StarredRepoOut.model_validate(r).model_dump()
        d["_score"] = round(float(score) * 100, 1)
        items.append(d)

    items.sort(key=lambda x: x["_score"], reverse=True)
    return Response.ok(data={"items": items[:20], "total": len(items)})


@router.delete("/repos/{repo_id}", response_model=Response)
def delete_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = db.execute(
        select(StarredRepo).where(StarredRepo.id == repo_id, StarredRepo.user_id == user.id)
    ).scalar_one_or_none()
    if repo is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Repo not found").model_dump_json())

    db.delete(repo)
    db.commit()
    return Response.ok(data={"deleted": repo_id})


# ── Import / Export ────────────────────────────────────────────────────────────

@router.post("/repos/import", response_model=Response)
def import_repos(
    body: GitHubImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "Use JSON file upload import instead").model_dump_json())


@router.post("/repos/import-json", response_model=Response)
async def import_repos_json(
    account_id: int = Form(0),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import repos from a JSON file. The JSON should be an array of repo objects."""
    if file is None:
        # Try reading from body as JSON
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "File is required").model_dump_json())

    content = await file.read()
    try:
        repos = json.loads(content.decode())
        if not isinstance(repos, list):
            raise ValueError("JSON must be an array")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, f"Invalid JSON: {str(e)}").model_dump_json())

    imported = 0
    skipped = 0
    for item in repos:
        full_name = item.get("repo_full_name") or item.get("full_name", "")
        if not full_name:
            continue
        exists = db.execute(
            select(StarredRepo).where(
                StarredRepo.user_id == user.id,
                StarredRepo.repo_full_name == full_name,
            )
        ).scalar_one_or_none()
        if exists:
            skipped += 1
            continue

        db.add(StarredRepo(
            user_id=user.id,
            account_id=account_id if account_id > 0 else None,
            repo_full_name=full_name,
            repo_name=item.get("repo_name") or item.get("name", full_name.split("/")[-1]),
            owner=item.get("owner", ""),
            description=item.get("description") or "",
            language=item.get("language") or "",
            stars=item.get("stars", 0),
            forks=item.get("forks", 0),
            repo_created_at=item.get("repo_created_at"),
            repo_updated_at=item.get("repo_updated_at"),
        ))
        imported += 1

    db.commit()
    return Response.ok(data={"imported": imported, "skipped": skipped})


@router.get("/repos/export", response_model=Response)
def export_repos(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = db.execute(
        select(StarredRepo).where(StarredRepo.user_id == user.id).order_by(StarredRepo.stars.desc())
    )
    repos = result.scalars().all()
    data = [StarredRepoOut.model_validate(r).model_dump() for r in repos]

    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return StreamingResponse(
        BytesIO(json_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=starred_repos.json"},
    )
