import json
import logging
import re
import threading

from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.bookmark import Bookmark
from app.services.ai_service import analyze_bookmark

logger = logging.getLogger(__name__)


def parse_bookmark_html(content: str) -> list[dict]:
    """Parse Netscape Bookmark HTML and return list of bookmark dicts with folder_path and date_added."""
    soup = BeautifulSoup(content, "html.parser")
    bookmarks = []
    folder_stack = []

    # Process all <DT> elements in document order
    dt_elements = soup.find_all("dt")
    # Track <dl> nesting by walking siblings inside each <dl>
    for dt in dt_elements:
        # Check if this DT contains an H3 (folder)
        h3 = dt.find("h3")
        if h3:
            folder_name = h3.get_text(strip=True)
            add_date = h3.get("add_date", "")
            folder_stack.append({"name": folder_name, "add_date": add_date})
            # Check if next sibling is a DL
            continue

        # Check if this DT contains an A (bookmark)
        a_tag = dt.find("a")
        if a_tag:
            url = a_tag.get("href", "").strip()
            title = a_tag.get_text(strip=True)
            add_date = a_tag.get("add_date", "")

            if not url or not title:
                continue

            folder_path = "/".join(f["name"] for f in folder_stack) if folder_stack else ""

            bookmarks.append({
                "url": url,
                "title": title,
                "folder_path": folder_path,
                "date_added": _convert_timestamp(add_date),
            })

        # Check if next siblings indicate closing of DL (folder end)
        # We detect this by looking at the DT's position relative to DL closings

    return bookmarks


def _convert_timestamp(ts: str) -> str:
    """Convert Unix timestamp (seconds or milliseconds) to readable date string."""
    if not ts:
        return ""
    try:
        from datetime import datetime, timezone
        t = int(ts)
        if t > 1e12:  # milliseconds
            t = t // 1000
        return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return ts


def import_bookmarks_with_ai(db, file_content: str, browser: str, user_id: int) -> int:
    """Import bookmarks from HTML content with background AI analysis."""
    bookmarks_data = parse_bookmark_html(file_content)
    imported_ids = []

    for bm_data in bookmarks_data:
        url = bm_data["url"][:2048]
        title = bm_data["title"][:512]

        existing = db.execute(
            select(Bookmark).where(Bookmark.url == url, Bookmark.user_id == user_id)
        ).scalar_one_or_none()
        if existing:
            continue

        category = f"imported/{browser}" if browser else "imported"

        bm = Bookmark(
            title=title,
            url=url,
            description="",
            author="",
            category=category,
            tags=json.dumps([], ensure_ascii=False),
            folder_path=bm_data.get("folder_path", ""),
            date_added=bm_data.get("date_added", ""),
            user_id=user_id,
        )
        db.add(bm)
        db.flush()  # Get the ID
        imported_ids.append(bm.id)

    db.add(AuditLog(user_id=user_id, action="import", target_type="bookmark", target_id=0))
    db.commit()

    if imported_ids:
        thread = threading.Thread(
            target=_ai_analysis_thread,
            args=(imported_ids,),
            daemon=True,
        )
        thread.start()

    return len(imported_ids)


def _ai_analysis_thread(bookmark_ids: list[int]):
    """Background thread to analyze bookmarks with AI."""
    db = SessionLocal()
    try:
        for bm_id in bookmark_ids:
            bm = db.query(Bookmark).get(bm_id)
            if not bm:
                continue

            try:
                result = analyze_bookmark(
                    url=bm.url,
                    bookmark_title=bm.title,
                    page_title=bm.page_title or "",
                    page_description=bm.page_description or "",
                    page_text=bm.page_text or "",
                )

                if result.get("generated_title"):
                    bm.generated_title = result["generated_title"]
                if result.get("generated_description"):
                    bm.generated_description = result["generated_description"]
                if result.get("crawl_error"):
                    bm.crawl_error = result["crawl_error"]

                # Update category from AI
                if result.get("category"):
                    bm.category = result["category"]

                # Update tags from AI
                if result.get("tags"):
                    tags_list = [t.strip() for t in result["tags"].split(",") if t.strip()]
                    bm.tags = json.dumps(tags_list, ensure_ascii=False)

                db.commit()
            except Exception as e:
                logger.error(f"AI analysis failed for bookmark {bm_id}: {e}")
                bm.crawl_error = str(e)[:500]
                db.commit()
    finally:
        db.close()
