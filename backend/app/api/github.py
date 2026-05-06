import json
import logging
import threading
from datetime import datetime, timezone
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
from app.models.recommended_repo import RecommendedRepo
from app.schemas import Response, ERROR_BAD_REQUEST, ERROR_NOT_FOUND
from app.schemas.github import GitHubAccountCreate, GitHubAccountOut, GitHubImportRequest, StarredRepoOut
from app.services.github_service import get_user_info, list_starred_repos, get_repo_detail, get_repo_readme, search_repos_by_topic, GitHubServiceError
from app.services.ai_service import analyze_repo

logger = logging.getLogger(__name__)

router = APIRouter()

# Progress tracking for background analysis tasks
_analysis_progress: dict[int, dict] = {}
# Progress tracking for recommendation generation
_recommendation_progress: dict[int, dict] = {}


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


# ── AI Analysis ─────────────────────────────────────────────────────────────────

def _run_analysis(user_id: int):
    """Background: fetch repo detail + README from GitHub (public API, no auth), analyze with AI, update DB."""
    task = _analysis_progress.get(user_id)
    if not task:
        return

    db = None
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()

        # Find unanalyzed repos
        result = db.execute(
            select(StarredRepo).where(
                StarredRepo.user_id == user_id,
                StarredRepo.ai_analyzed_at.is_(None),
            ).order_by(StarredRepo.stars.desc())
        )
        repos = result.scalars().all()

        total = len(repos)
        task["total"] = total
        task["status"] = "running"
        task["current"] = 0
        task["message"] = f"Found {total} repos to analyze"

        for i, repo in enumerate(repos):
            task["current"] = i + 1
            task["message"] = f"Analyzing {repo.repo_full_name} ({i+1}/{total})"

            try:
                # Fetch detail from GitHub
                detail = get_repo_detail(repo.repo_full_name)
                # Fetch README
                readme = get_repo_readme(repo.repo_full_name, max_chars=3000)

                # AI analysis
                ai = analyze_repo(
                    repo_full_name=repo.repo_full_name,
                    description=detail.get("description", ""),
                    topics=detail.get("topics", ""),
                    language=detail.get("language", ""),
                    readme_text=readme,
                    homepage=detail.get("homepage", ""),
                )

                # Update repo with fetched detail + AI results
                repo.language_color = detail.get("language_color", "")
                repo.open_issues = detail.get("open_issues", 0)
                repo.watchers = detail.get("watchers", 0)
                repo.size_kb = detail.get("size_kb", 0)
                repo.topics = detail.get("topics", "")
                repo.homepage = detail.get("homepage", "")
                repo.license = detail.get("license", "")
                repo.default_branch = detail.get("default_branch", "")
                repo.archived = detail.get("archived", False)
                repo.readme_text = readme
                repo.ai_tags = ai.get("ai_tags", "")
                repo.ai_summary = ai.get("ai_summary", "")
                repo.ai_category = ai.get("ai_category", "")
                repo.ai_analyzed_at = datetime.now(timezone.utc).isoformat()
                repo.analyze_error = ai.get("crawl_error", "")

                db.commit()

                task["analyzed_repos"].append({
                    "id": repo.id,
                    "repo_full_name": repo.repo_full_name,
                    "ai_tags": repo.ai_tags,
                    "ai_summary": repo.ai_summary,
                    "ai_category": repo.ai_category,
                })

            except GitHubServiceError as e:
                repo.analyze_error = str(e)
                repo.ai_analyzed_at = datetime.now(timezone.utc).isoformat()
                db.commit()
            except Exception as e:
                logger.error(f"Failed to analyze repo {repo.repo_full_name}: {e}")
                repo.analyze_error = str(e)[:500]
                repo.ai_analyzed_at = datetime.now(timezone.utc).isoformat()
                db.commit()

        task["status"] = "completed"
        task["message"] = f"Analysis complete: {total} repos processed"
        task["finished_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        logger.error(f"Analysis task failed for user {user_id}: {e}")
        if user_id in _analysis_progress:
            _analysis_progress[user_id]["status"] = "failed"
            _analysis_progress[user_id]["message"] = str(e)[:500]
    finally:
        if db:
            db.close()


@router.post("/repos/analyze-all", response_model=Response)
def analyze_all_repos(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start background AI analysis for all unanalyzed starred repos."""
    # Get a valid GitHub token
    account = db.execute(
        select(GitHubAccount).where(
            GitHubAccount.user_id == user.id,
            GitHubAccount.is_deleted == False,
        ).order_by(GitHubAccount.created_at.desc())
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "No GitHub account linked").model_dump_json())

    # Check if already running
    if user.id in _analysis_progress and _analysis_progress[user.id].get("status") == "running":
        return Response.ok(data={"message": "Analysis already in progress", "progress": _analysis_progress[user.id]})

    _analysis_progress[user.id] = {
        "status": "starting",
        "total": 0,
        "current": 0,
        "message": "Starting analysis...",
        "analyzed_repos": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    thread = threading.Thread(
        target=_run_analysis,
        args=(user.id,),
        daemon=True,
    )
    thread.start()

    return Response.ok(data={"message": "Analysis started", "progress": _analysis_progress[user.id]})


@router.get("/repos/analyze-progress", response_model=Response)
def analyze_progress(
    user: User = Depends(get_current_user),
):
    """Poll analysis progress."""
    task = _analysis_progress.get(user.id)
    if not task:
        return Response.ok(data={"status": "idle", "message": "No analysis task found"})
    return Response.ok(data=task)


# ── Recommendations ────────────────────────────────────────────────────────────

def _run_recommendation(user_id: int, top_k_tags: int):
    """Background: extract user's tag profile, search public GitHub, score, store recommendations."""
    task = _recommendation_progress.get(user_id)
    if not task:
        return

    db = None
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()

        # Step 1: Extract user's tag profile from analyzed repos
        # Prefer ai_tags; fall back to GitHub topics (which are stored as JSON array string)
        result = db.execute(
            select(StarredRepo).where(
                StarredRepo.user_id == user_id,
                StarredRepo.ai_analyzed_at.isnot(None),
            )
        )
        analyzed = result.scalars().all()

        if not analyzed:
            task["status"] = "failed"
            task["message"] = "No analyzed repos found. Run analyze-all first."
            return

        # Count tag frequency
        import re
        tag_freq: dict[str, int] = {}
        for repo in analyzed:
            # Try ai_tags first, then GitHub topics
            tag_source = repo.ai_tags if repo.ai_tags else repo.topics
            if not tag_source:
                continue
            # GitHub topics stored as JSON array string: '["topic1","topic2"]'
            if tag_source.startswith("["):
                try:
                    tags = json.loads(tag_source)
                except (json.JSONDecodeError, TypeError):
                    tags = [t.strip() for t in tag_source.strip("[]").split(",") if t.strip()]
            else:
                tags = [t.strip() for t in tag_source.split(",") if t.strip()]
            for tag in tags:
                tag = tag.strip().strip('"').strip("'")
                if tag:
                    tag_freq[tag] = tag_freq.get(tag, 0) + 1

        sorted_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:top_k_tags]

        task["status"] = "running"
        task["total"] = len(top_tags)
        task["current"] = 0
        task["message"] = f"Top tags: {', '.join(t[0] for t in top_tags)}"
        task["top_tags"] = [{"tag": t, "count": c} for t, c in top_tags]
        task["found_repos"] = []

        # Get user's existing starred repos
        existing = db.execute(
            select(StarredRepo.repo_full_name).where(StarredRepo.user_id == user_id)
        )
        existing_full_names = {r[0] for r in existing.all()}

        # Get already-recommended repos
        already_rec = db.execute(
            select(RecommendedRepo.repo_full_name).where(RecommendedRepo.user_id == user_id)
        )
        already_rec_names = {r[0] for r in already_rec.all()}

        for i, (tag, count) in enumerate(top_tags):
            task["current"] = i + 1
            task["message"] = f"Searching repos for tag: {tag} ({i+1}/{len(top_tags)})"

            # Step 2: Search GitHub for repos matching this tag
            try:
                search_results = search_repos_by_topic(tag, per_page=10)
            except GitHubServiceError as e:
                task["message"] = f"Search failed for tag {tag}: {e}"
                continue

            # Step 3: Deduplicate and enrich
            new_count = 0
            for sr in search_results:
                full_name = sr.get("repo_full_name", "")
                if not full_name:
                    continue
                if full_name in existing_full_names or full_name in already_rec_names:
                    continue

                # Enrich with full repo detail
                try:
                    detail = get_repo_detail(full_name)
                except GitHubServiceError:
                    detail = sr

                # Simple scoring: star weight + tag match
                stars = detail.get("stars", sr.get("stars", 0))
                # Normalize score: stars / 1000, capped at 10
                score = min(stars / 1000.0, 10.0)

                recommended_repo = RecommendedRepo(
                    user_id=user_id,
                    repo_full_name=full_name,
                    repo_name=sr.get("repo_name", full_name.split("/")[-1]),
                    owner=sr.get("owner", ""),
                    html_url=sr.get("html_url", ""),
                    clone_url=sr.get("clone_url", ""),
                    description=detail.get("description", ""),
                    topics=detail.get("topics", ""),
                    language=detail.get("language", ""),
                    language_color=detail.get("language_color", ""),
                    stars=stars,
                    forks=detail.get("forks", sr.get("forks", 0)),
                    open_issues=detail.get("open_issues", sr.get("open_issues", 0)),
                    watchers=detail.get("watchers", sr.get("watchers", 0)),
                    license=detail.get("license", ""),
                    homepage=detail.get("homepage", ""),
                    default_branch=detail.get("default_branch", ""),
                    size_kb=detail.get("size_kb", sr.get("size_kb", 0)),
                    archived=detail.get("archived", False),
                    score=round(score, 2),
                    match_tags=tag,
                    source_tag=tag,
                    recommend_reason=f"匹配你的兴趣标签「{tag}」(频次: {count})",
                    recommended_at=datetime.now(timezone.utc).isoformat(),
                )

                try:
                    db.add(recommended_repo)
                    db.commit()
                    already_rec_names.add(full_name)
                    new_count += 1

                    task["found_repos"].append({
                        "repo_full_name": full_name,
                        "repo_name": sr.get("repo_name", ""),
                        "stars": stars,
                        "source_tag": tag,
                        "score": round(score, 2),
                    })
                except Exception:
                    db.rollback()
                    already_rec_names.add(full_name)  # Skip duplicates in same run

            task["message"] = f"Tag '{tag}': found {len(search_results)} results, {new_count} new"

        total_found = len(task["found_repos"])
        task["status"] = "completed"
        task["message"] = f"Recommendation complete: {total_found} new repos from {len(top_tags)} tags"
        task["finished_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        logger.error(f"Recommendation failed for user {user_id}: {e}")
        if user_id in _recommendation_progress:
            _recommendation_progress[user_id]["status"] = "failed"
            _recommendation_progress[user_id]["message"] = str(e)[:500]
    finally:
        if db:
            db.close()


@router.post("/repos/generate-recommendations", response_model=Response)
def generate_recommendations(
    body: dict | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate recommended repos based on user's analyzed tag profile."""
    top_k_tags = 3
    if body and isinstance(body, dict):
        top_k_tags = body.get("top_k_tags", 3)
        top_k_tags = max(1, min(5, int(top_k_tags)))

    # Get a valid GitHub token
    account = db.execute(
        select(GitHubAccount).where(
            GitHubAccount.user_id == user.id,
            GitHubAccount.is_deleted == False,
        ).order_by(GitHubAccount.created_at.desc())
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=400, detail=Response.error(ERROR_BAD_REQUEST, "No GitHub account linked").model_dump_json())

    # Check if already running
    if user.id in _recommendation_progress and _recommendation_progress[user.id].get("status") == "running":
        return Response.ok(data={"message": "Recommendation already in progress", "progress": _recommendation_progress[user.id]})

    _recommendation_progress[user.id] = {
        "status": "starting",
        "total": 0,
        "current": 0,
        "message": "Starting recommendation...",
        "top_tags": [],
        "found_repos": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    thread = threading.Thread(
        target=_run_recommendation,
        args=(user.id, top_k_tags),
        daemon=True,
    )
    thread.start()

    return Response.ok(data={"message": "Recommendation started", "progress": _recommendation_progress[user.id]})


@router.get("/repos/recommendations-progress", response_model=Response)
def recommendations_progress(
    user: User = Depends(get_current_user),
):
    """Poll recommendation generation progress."""
    task = _recommendation_progress.get(user.id)
    if not task:
        return Response.ok(data={"status": "idle", "message": "No recommendation task found"})
    return Response.ok(data=task)


@router.get("/repos/recommendations/sse")
async def recommendations_sse(
    user: User = Depends(get_current_user),
):
    """SSE endpoint: stream when new recommendations are available."""
    import asyncio

    async def event_stream():
        from app.schemas.github import RecommendedRepoOut
        from app.core.database import SessionLocal

        last_total = 0
        while True:
            db = SessionLocal()
            try:
                result = db.execute(
                    select(RecommendedRepo).where(RecommendedRepo.user_id == user.id)
                )
                repos = result.scalars().all()

                total = len(repos)
                if total > last_total:
                    new_count = total - last_total
                    last_total = total
                    new_repos = result.scalars().all()[:new_count]
                    data = [RecommendedRepoOut.model_validate(r).model_dump() for r in new_repos]
                    yield f"data: {json.dumps({'new_count': new_count, 'total': total, 'items': data}, ensure_ascii=False)}\n\n"
                else:
                    yield f": heartbeat\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
            finally:
                db.close()
            await asyncio.sleep(30)  # Check every 30 seconds

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/repos/recommendations", response_model=Response)
def list_recommendations(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List recommended repos for the user."""
    from app.schemas.github import RecommendedRepoOut

    count_stmt = select(func.count()).select_from(
        select(RecommendedRepo).where(RecommendedRepo.user_id == user.id).subquery()
    )
    total = db.execute(count_stmt).scalar() or 0

    result = db.execute(
        select(RecommendedRepo)
        .where(RecommendedRepo.user_id == user.id)
        .order_by(RecommendedRepo.score.desc(), RecommendedRepo.recommended_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    repos = result.scalars().all()

    data = [RecommendedRepoOut.model_validate(r).model_dump() for r in repos]
    return Response.ok(data={"items": data, "total": total, "page": page, "page_size": page_size})


# ── Single Repo (catch-all, must come after specific routes) ────────────────────

@router.get("/repos/{repo_id}", response_model=Response)
def get_repo(
    repo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single starred repo with all details."""
    repo = db.execute(
        select(StarredRepo).where(StarredRepo.id == repo_id, StarredRepo.user_id == user.id)
    ).scalar_one_or_none()
    if repo is None:
        raise HTTPException(status_code=404, detail=Response.error(ERROR_NOT_FOUND, "Repo not found").model_dump_json())
    return Response.ok(data=StarredRepoOut.model_validate(repo).model_dump())


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
