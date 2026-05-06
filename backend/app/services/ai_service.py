import json
import logging
from typing import Optional

from anthropic import Anthropic
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


def _get_config() -> Optional[dict]:
    db = SessionLocal()
    try:
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "api_endpoint")).scalar_one_or_none()
        endpoint = result.value.strip() if result and result.value else None
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "api_key")).scalar_one_or_none()
        api_key = result.value.strip() if result and result.value else None
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "api_provider")).scalar_one_or_none()
        provider = result.value.strip() if result and result.value else "openai"
        result = db.execute(select(SystemConfig).where(SystemConfig.key == "ai_model")).scalar_one_or_none()
        model = result.value.strip() if result and result.value else "default"

        if not endpoint or not api_key:
            return None

        return {"endpoint": endpoint, "api_key": api_key, "provider": provider, "model": model}
    except Exception as e:
        logger.error(f"Failed to read AI config: {e}")
        return None
    finally:
        db.close()


REPO_SYSTEM_PROMPT = """你是一个 GitHub 项目分析助手。根据提供的项目信息，分析并返回结构化的 JSON 数据。

要求：
1. ai_tags: 4-8 个技术标签，逗号分隔，标签要能准确反映项目的技术栈、领域和用途（如"机器学习,Python,NLP,Transformer"）
2. ai_summary: 用 2-3 句话概括项目功能和特点（中文，100字以内）
3. ai_category: 两级分类，格式为"大类/小类"，例如"AI/自然语言处理"、"Web/前端框架"、"DevOps/容器化"
4. crawl_error: 如果无法分析则填写错误原因，否则留空字符串

你必须严格按以下 JSON 格式返回，不要包含任何其他文字：
{
  "ai_tags": "tag1,tag2,tag3",
  "ai_summary": "...",
  "ai_category": "大类/小类",
  "crawl_error": ""
}"""


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
    user_content = f"""URL: {url}
书签标题: {bookmark_title}
网页标题: {page_title}
网页描述: {page_description}
网页正文摘要: {page_text[:2000]}"""

    cfg = _get_config()
    if not cfg:
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": "AI service not configured",
        }

    if cfg["provider"] == "anthropic":
        return _call_anthropic(cfg, user_content)
    else:
        return _call_openai(cfg, user_content)


def analyze_repo(
    repo_full_name: str,
    description: str = "",
    topics: str = "",
    language: str = "",
    readme_text: str = "",
    homepage: str = "",
) -> dict:
    """Analyze GitHub repository and return structured tags/summary/category.

    Returns dict with: ai_tags, ai_summary, ai_category, crawl_error
    """
    user_content = f"""项目名称: {repo_full_name}
语言: {language}
描述: {description}
GitHub Topics: {topics}
主页: {homepage}
README 摘要: {readme_text[:2000]}"""

    cfg = _get_config()
    if not cfg:
        return {
            "ai_tags": "",
            "ai_summary": "",
            "ai_category": "",
            "crawl_error": "AI service not configured",
        }

    if cfg["provider"] == "anthropic":
        return _call_anthropic_repo(cfg, user_content)
    else:
        return _call_openai_repo(cfg, user_content)


def _call_openai_repo(cfg: dict, user_content: str) -> dict:
    client = OpenAI(base_url=cfg["endpoint"], api_key=cfg["api_key"], timeout=120)
    try:
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": REPO_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content.strip()
        return _parse_repo_json_response(content)
    except Exception as e:
        logger.error(f"OpenAI repo call failed: {e}")
        return {"ai_tags": "", "ai_summary": "", "ai_category": "", "crawl_error": str(e)[:500]}


def _call_anthropic_repo(cfg: dict, user_content: str) -> dict:
    endpoint = cfg["endpoint"]
    if endpoint.endswith("/v1"):
        endpoint = endpoint[:-3]
    elif endpoint.endswith("/v1/"):
        endpoint = endpoint[:-4]
    client = Anthropic(api_key=cfg["api_key"], base_url=endpoint, timeout=120)
    try:
        response = client.messages.create(
            model=cfg["model"],
            max_tokens=1024,
            temperature=0.3,
            system=REPO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        content = "".join(block.text for block in response.content if block.type == "text").strip()
        return _parse_repo_json_response(content)
    except Exception as e:
        logger.error(f"Anthropic repo call failed: {e}")
        return {"ai_tags": "", "ai_summary": "", "ai_category": "", "crawl_error": str(e)[:500]}


def _parse_repo_json_response(content: str) -> dict:
    try:
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        result = json.loads(content)
        return {
            "ai_tags": result.get("ai_tags", ""),
            "ai_summary": result.get("ai_summary", ""),
            "ai_category": result.get("ai_category", ""),
            "crawl_error": result.get("crawl_error", ""),
        }
    except json.JSONDecodeError as e:
        logger.warning(f"AI returned invalid JSON for repo: {content[:200]}")
        return {
            "ai_tags": "",
            "ai_summary": "",
            "ai_category": "",
            "crawl_error": f"AI response parse error: {str(e)}",
        }


def _call_openai(cfg: dict, user_content: str) -> dict:
    client = OpenAI(base_url=cfg["endpoint"], api_key=cfg["api_key"], timeout=120)
    try:
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content.strip()
        return _parse_json_response(content)
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": str(e)[:500],
        }


def _call_anthropic(cfg: dict, user_content: str) -> dict:
    endpoint = cfg["endpoint"]
    # Anthropic SDK >=0.50 auto-appends /v1, so strip it from user config
    if endpoint.endswith("/v1"):
        endpoint = endpoint[:-3]
    elif endpoint.endswith("/v1/"):
        endpoint = endpoint[:-4]
    client = Anthropic(api_key=cfg["api_key"], base_url=endpoint, timeout=120)
    try:
        response = client.messages.create(
            model=cfg["model"],
            max_tokens=1024,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_content},
            ],
        )
        content = "".join(block.text for block in response.content if block.type == "text").strip()
        return _parse_json_response(content)
    except Exception as e:
        logger.error(f"Anthropic call failed: {e}")
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": str(e)[:500],
        }


def _parse_json_response(content: str) -> dict:
    try:
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
        logger.warning(f"AI returned invalid JSON: {content[:200]}")
        return {
            "generated_title": "",
            "generated_description": "",
            "tags": "",
            "category": "",
            "crawl_error": f"AI response parse error: {str(e)}",
        }
