import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubServiceError(Exception):
    pass


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BookmarkRecommender/1.0",
    }


def get_user_info(token: str) -> dict:
    """Validate token and return authenticated user info."""
    r = requests.get(f"{GITHUB_API}/user", headers=_headers(token), timeout=15)
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
        headers=_headers(token),
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


def star_repo(token: str, repo_full_name: str) -> None:
    """Star a repository."""
    r = requests.put(
        f"{GITHUB_API}/user/starred/{repo_full_name}",
        headers=_headers(token),
        timeout=15,
    )
    if r.status_code not in (204, 304):
        raise GitHubServiceError(f"Failed to star repo: {r.status_code} {r.text[:200]}")


def unstar_repo(token: str, repo_full_name: str) -> None:
    """Unstar a repository."""
    r = requests.delete(
        f"{GITHUB_API}/user/starred/{repo_full_name}",
        headers=_headers(token),
        timeout=15,
    )
    if r.status_code not in (204, 304):
        raise GitHubServiceError(f"Failed to unstar repo: {r.status_code} {r.text[:200]}")
