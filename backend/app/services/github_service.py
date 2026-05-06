import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubServiceError(Exception):
    pass


def _auth_headers(token: str) -> dict:
    """Headers with authentication — for user-specific operations only."""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookmarkRecommender/1.0",
    }


def _public_headers() -> dict:
    """Headers without authentication — for public read-only API calls."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookmarkRecommender/1.0",
    }


def get_user_info(token: str) -> dict:
    """Validate token and return authenticated user info."""
    r = requests.get(f"{GITHUB_API}/user", headers=_auth_headers(token), timeout=15)
    if r.status_code == 401:
        raise GitHubServiceError("Invalid GitHub token")
    if r.status_code != 200:
        raise GitHubServiceError(f"GitHub API error: {r.status_code} {r.text[:200]}")
    data = r.json()
    return {
        "github_login": data.get("login", ""),
        "avatar_url": data.get("avatar_url", ""),
    }


def list_starred_repos(token: str, page: int = 1, per_page: int = 100) -> tuple[list[dict], str | None]:
    """List starred repos for the authenticated user. Returns (repos, next_page_url)."""
    params = {"page": page, "per_page": min(per_page, 100)}
    r = requests.get(
        f"{GITHUB_API}/user/starred",
        headers=_auth_headers(token),
        params=params,
        timeout=30,
    )
    if r.status_code != 200:
        raise GitHubServiceError(f"Failed to list starred repos: {r.status_code} {r.text[:200]}")

    repos = []
    for item in r.json():
        repo = item.get("repo") or item
        repos.append({
            "repo_full_name": repo.get("full_name", ""),
            "repo_name": repo.get("name", ""),
            "owner": repo.get("owner", {}).get("login", "") if repo.get("owner") else "",
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "repo_created_at": repo.get("created_at"),
            "repo_updated_at": repo.get("updated_at"),
        })

    next_link = None
    link_header = r.headers.get("Link", "")
    for part in link_header.split(","):
        if 'rel="next"' in part:
            next_link = part.split(";")[0].strip(" <>")
            break

    return repos, next_link


def get_repo_detail(repo_full_name: str) -> dict:
    """Get public repository information (no auth needed)."""
    r = requests.get(
        f"{GITHUB_API}/repos/{repo_full_name}",
        headers=_public_headers(),
        timeout=15,
    )
    if r.status_code != 200:
        raise GitHubServiceError(f"Failed to get repo detail: {r.status_code} {r.text[:200]}")
    repo = r.json()
    license_name = ""
    if repo.get("license") and repo["license"] is not None:
        license_name = repo["license"].get("spdx_id", "")
    return {
        "description": repo.get("description") or "",
        "language": repo.get("language") or "",
        "language_color": "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "watchers": repo.get("watchers_count", 0),
        "size_kb": repo.get("size", 0),
        "topics": json_dumps(repo.get("topics", [])),
        "homepage": repo.get("homepage") or "",
        "license": license_name,
        "default_branch": repo.get("default_branch", ""),
        "archived": repo.get("archived", False),
        "repo_created_at": repo.get("created_at"),
        "repo_updated_at": repo.get("updated_at"),
    }


def get_repo_readme(repo_full_name: str, max_chars: int = 3000) -> str:
    """Get the README content for a public repository (no auth needed)."""
    try:
        r = requests.get(
            f"{GITHUB_API}/repos/{repo_full_name}/readme",
            headers=_public_headers(),
            timeout=15,
        )
        if r.status_code != 200:
            return ""
        import base64
        content = r.json().get("content", "")
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        return decoded[:max_chars]
    except Exception as e:
        logger.warning(f"Failed to fetch README for {repo_full_name}: {e}")
        return ""


def search_repos_by_topic(topic: str, per_page: int = 10, page: int = 1) -> list[dict]:
    """Search public GitHub repositories by topic (no auth, 10 req/min rate limit)."""
    params = {
        "q": f"topic:{topic}",
        "sort": "stars",
        "order": "desc",
        "per_page": min(per_page, 30),
        "page": page,
    }
    r = requests.get(
        f"{GITHUB_API}/search/repositories",
        headers=_public_headers(),
        params=params,
        timeout=30,
    )
    if r.status_code != 200:
        raise GitHubServiceError(f"Search failed: {r.status_code} {r.text[:200]}")
    items = r.json().get("items", [])
    results = []
    for repo in items:
        license_name = ""
        if repo.get("license") and repo["license"] is not None:
            license_name = repo["license"].get("spdx_id", "")
        results.append({
            "repo_full_name": repo.get("full_name", ""),
            "repo_name": repo.get("name", ""),
            "owner": repo.get("owner", {}).get("login", "") if repo.get("owner") else "",
            "html_url": repo.get("html_url", ""),
            "clone_url": repo.get("clone_url", ""),
            "description": repo.get("description") or "",
            "topics": json_dumps(repo.get("topics", [])),
            "language": repo.get("language") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "watchers": repo.get("watchers_count", 0),
            "license": license_name,
            "homepage": repo.get("homepage") or "",
            "default_branch": repo.get("default_branch", ""),
            "size_kb": repo.get("size", 0),
            "archived": repo.get("archived", False),
            "repo_created_at": repo.get("created_at"),
            "repo_updated_at": repo.get("updated_at"),
        })
    return results


def json_dumps(obj) -> str:
    import json as _json
    return _json.dumps(obj, ensure_ascii=False)


def star_repo(token: str, repo_full_name: str) -> None:
    """Star a repository."""
    r = requests.put(
        f"{GITHUB_API}/user/starred/{repo_full_name}",
        headers=_auth_headers(token),
        timeout=15,
    )
    if r.status_code not in (204, 304):
        raise GitHubServiceError(f"Failed to star repo: {r.status_code} {r.text[:200]}")


def unstar_repo(token: str, repo_full_name: str) -> None:
    """Unstar a repository."""
    r = requests.delete(
        f"{GITHUB_API}/user/starred/{repo_full_name}",
        headers=_auth_headers(token),
        timeout=15,
    )
    if r.status_code not in (204, 304):
        raise GitHubServiceError(f"Failed to unstar repo: {r.status_code} {r.text[:200]}")
