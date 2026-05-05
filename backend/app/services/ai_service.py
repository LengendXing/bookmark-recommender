import json
import logging
from typing import Optional

from openai import OpenAI
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个网页内容分析助手。根据提供的网页信息，分析并返回结构化的 JSON 数据。

要求：
1. generated_title: 用中文重新提炼一个简洁准确的标题（15字以内）
2. generated_description: 用 2-3 句话概括网页核心内容（中文，80字以内）
3. tags: 4-8 个中文标签，逗号分隔，标签要能准确反映网页主题和内容类型
4. category: 两级分类，格式为"大类/小类"，例如"编程语言/Python"、"安全/Web安全"
5. crawl_error: 如果无法分析则填写错误原因，否则留空字符串

你必须严格按以下 JSON 格式返回，不要包含任何其他文字：
{
  "generated_title": "...",
  "generated_description": "...",
  "tags": "tag1,tag2,tag3",
  "category": "大类/小类",
  "crawl_error": ""
}"""


def _get_client() -> Optional[OpenAI]:
    db = SessionLocal()
    try:
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "api_endpoint")).scalar_one_or_none()
        endpoint = result.value.strip() if result and result.value else None
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "api_key")).scalar_one_or_none()
        api_key = result.value.strip() if result and result.value else None

        if not endpoint or not api_key:
            return None

        return OpenAI(base_url=endpoint, api_key=api_key, timeout=30)
    except Exception as e:
        logger.error(f"Failed to create AI client: {e}")
        return None
    finally:
        db.close()


def analyze_bookmark(
    url: str,
    bookmark_title: str,
    page_title: str = "",
    page_description: str = "",
    page_text: str = "",
) -> dict:
    """Analyze bookmark content and return structured data.

    Returns dict with: generated_title, generated_description, tags, category, crawl_error
    """
    client = _get_client()
    if not client:
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": "AI service not configured",
        }

    user_content = f"""URL: {url}
书签标题: {bookmark_title}
网页标题: {page_title}
网页描述: {page_description}
网页正文摘要: {page_text[:2000]}"""

    try:
        response = client.chat.completions.create(
            model="default",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content.strip()

        # Handle JSON in markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        return {
            "generated_title": result.get("generated_title", ""),
            "generated_description": result.get("generated_description", ""),
            "tags": result.get("tags", ""),
            "category": result.get("category", ""),
            "crawl_error": result.get("crawl_error", ""),
        }
    except json.JSONDecodeError as e:
        logger.warning(f"AI returned invalid JSON for {url}: {content[:200]}")
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": f"AI response parse error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"AI analysis failed for {url}: {e}")
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": str(e)[:500],
        }
