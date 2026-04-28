import json
from typing import Optional

from anthropic import AsyncAnthropic

from app.core.config import get_settings

settings = get_settings()
_client: Optional[AsyncAnthropic] = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def enrich_bookmark(title: str, description: str, content_preview: str) -> dict:
    client = _get_client()
    prompt = (
        f"Given this webpage, return JSON with fields: category (one word), tags (up to 5 keywords), "
        f"a short description (2 sentences), and author (if detectable).\n"
        f"Title: {title}\nDescription: {description}\nPreview: {content_preview[:500]}"
    )
    resp = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text if resp.content else "{}"
    text = text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"category": "", "tags": [], "description": description, "author": ""}


async def generate_tags(text: str) -> list[str]:
    client = _get_client()
    prompt = f"Return a JSON array of up to 5 keyword tags for this text: {text[:300]}"
    resp = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text_out = resp.content[0].text if resp.content else "[]"
    text_out = text_out.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        tags = json.loads(text_out)
        return tags if isinstance(tags, list) else []
    except json.JSONDecodeError:
        return []
