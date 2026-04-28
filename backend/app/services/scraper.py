import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup


class ScrapedPage:
    def __init__(self, url: str, title: str, description: str, content_preview: str, author: str):
        self.url = url
        self.title = title
        self.description = description
        self.content_preview = content_preview
        self.author = author


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)


async def scrape_page(url: str, timeout: int = 15) -> ScrapedPage:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        resp = await client.get(url, headers={"User-Agent": "BookmarkRecommender/0.1"})
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()

    description = ""
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        description = og_desc["content"].strip()
    else:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

    author = ""
    og_author = soup.find("meta", property="author")
    if og_author and og_author.get("content"):
        author = og_author["content"].strip()
    else:
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()

    content_preview = clean_html(str(soup.find("body") or ""))[:500]

    return ScrapedPage(url=url, title=title, description=description, content_preview=content_preview, author=author)
