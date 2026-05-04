import json
import structlog

from sqlalchemy import select

from app.models.bookmark import Bookmark
from app.models.audit_log import AuditLog
from app.services.scraper import scrape_page, ScrapedPage
from app.services.claude_service import enrich_bookmark

logger = structlog.get_logger()


def ingest_single(db, url: str, user_id: int) -> Bookmark:
    existing = db.execute(select(Bookmark).where(Bookmark.url == url)).scalar_one_or_none()
    if existing:
        return existing

    scraped: ScrapedPage = scrape_page(url)
    logger.info("scraped", url=url, title=scraped.title)

    enriched = enrich_bookmark(scraped.title, scraped.description, scraped.content_preview)

    tags = enriched.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    bookmark = Bookmark(
        title=scraped.title or enriched.get("title", ""),
        url=url,
        description=enriched.get("description", scraped.description),
        author=enriched.get("author", scraped.author),
        content_preview=scraped.content_preview,
        category=enriched.get("category", ""),
        tags=json.dumps(tags, ensure_ascii=False),
        user_id=user_id,
    )
    db.add(bookmark)

    log = AuditLog(
        user_id=user_id,
        action="ingest",
        target_type="bookmark",
        target_id=0,
        details=json.dumps({"url": url}),
    )
    db.add(log)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def ingest_bulk(db, urls: list[str], user_id: int) -> list[Bookmark]:
    results = []
    for url in urls:
        try:
            bm = ingest_single(db, url, user_id)
            results.append(bm)
        except Exception as e:
            logger.error("ingest_failed", url=url, error=str(e))
    return results
