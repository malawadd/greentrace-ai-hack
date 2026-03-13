from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.schemas.company_esg import ArticleResult, CompanyEsgResponse


TRACKING_QUERY_KEYS = {"srsltid", "gclid", "fbclid"}
CONTENT_KEYS = ("content", "text", "markdown", "htmlMarkdown", "description")
URL_KEYS = ("url", "loadedUrl", "requestUrl", "finalUrl")
TITLE_KEYS = ("title", "pageTitle", "headline")


def build_company_response(company: str, payload: dict[str, Any]) -> CompanyEsgResponse:
    title_map = _build_title_map(payload)
    articles = _build_articles(payload, title_map)
    return CompanyEsgResponse(
        company=company,
        overall_status=str(payload.get("overall_status") or "unknown"),
        article_count=len(articles),
        articles=articles,
    )


def _build_articles(payload: dict[str, Any], title_map: dict[str, str]) -> list[ArticleResult]:
    article_map: dict[str, ArticleResult] = {}
    for item in payload.get("jina_results", []):
        article = _from_jina_item(item, title_map)
        if article:
            article_map[_normalize_url(article.url)] = article
    for item in payload.get("crawler_results", []):
        article = _from_crawler_item(item, title_map)
        if article:
            article_map.setdefault(_normalize_url(article.url), article)
    return list(article_map.values())


def _build_title_map(payload: dict[str, Any]) -> dict[str, str]:
    title_map: dict[str, str] = {}
    for result in payload.get("google_results", []):
        for organic in result.get("organicResults", []) or []:
            url = organic.get("url")
            title = organic.get("title")
            if url and title and _is_valid_url(url):
                title_map[_normalize_url(url)] = str(title)
    return title_map


def _from_jina_item(item: dict[str, Any], title_map: dict[str, str]) -> ArticleResult | None:
    url = item.get("url")
    content = item.get("content")
    if not isinstance(url, str) or not _is_valid_url(url) or not isinstance(content, str) or not content.strip():
        return None
    normalized = _normalize_url(url)
    title = title_map.get(normalized) or _extract_title_from_content(content)
    return ArticleResult(title=title, url=url, content=content.strip(), source="jina")


def _from_crawler_item(item: dict[str, Any], title_map: dict[str, str]) -> ArticleResult | None:
    url = next((item.get(key) for key in URL_KEYS if isinstance(item.get(key), str)), None)
    if not isinstance(url, str) or not _is_valid_url(url):
        return None
    content = next((item.get(key) for key in CONTENT_KEYS if isinstance(item.get(key), str) and item.get(key).strip()), None)
    if not isinstance(content, str):
        return None
    normalized = _normalize_url(url)
    title = title_map.get(normalized)
    if not title:
        title = next((item.get(key) for key in TITLE_KEYS if isinstance(item.get(key), str) and item.get(key).strip()), None)
    if not title and isinstance(item.get("metadata"), dict):
        meta_title = item["metadata"].get("title")
        if isinstance(meta_title, str) and meta_title.strip():
            title = meta_title.strip()
    return ArticleResult(title=title, url=url, content=content.strip(), source="crawler")


def _extract_title_from_content(content: str) -> str | None:
    first_line = content.splitlines()[0].strip() if content.splitlines() else ""
    if first_line.lower().startswith("title:"):
        return first_line.split(":", 1)[1].strip() or None
    return None


def _is_valid_url(value: str) -> bool:
    if " › " in value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    filtered = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS and not key.lower().startswith("utm_")
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(filtered), ""))