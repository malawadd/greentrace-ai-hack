from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

from apify import Actor

DEFAULT_COMPANY = 'H&M'
DEFAULT_QUERY_SUFFIX = 'ESG sustainability greenwashing 2024 2025'
DEFAULT_KEYWORD_TERMS = [
    'esg',
    'sustainability',
    'greenwashing',
    'climate',
    'emissions',
    'governance',
]
DEFAULT_JINA_ENGINE = 'direct'
DEFAULT_JINA_TIMEOUT_SECS = 200
SKIPPED_FILE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.svg',
    '.webp',
    '.ico',
    '.css',
    '.js',
    '.json',
    '.xml',
    '.pdf',
    '.zip',
    '.mp4',
    '.mp3',
}
URL_PATTERN = re.compile(r'https?://[^\s<>"\'\]\)]+', re.IGNORECASE)
ALLOWED_JINA_ENGINES = {'direct', 'browser'}


def coerce_positive_int(value: Any, default: int) -> int:
    try:
        coerced = int(value)
    except (TypeError, ValueError):
        return default

    return max(coerced, 1)


def coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes', 'y', 'on'}:
            return True
        if normalized in {'false', '0', 'no', 'n', 'off'}:
            return False
    return bool(value)


def normalize_text(value: Any, default: str = '') -> str:
    if value is None:
        return default

    text = str(value).strip()
    return text or default


def status_to_string(value: Any) -> str:
    if hasattr(value, 'value'):
        return str(value.value)
    return str(value)


def run_finished_successfully(run_status: str | None) -> bool:
    return (run_status or '').upper() == 'SUCCEEDED'


def build_query(company: str, query_suffix: str) -> str:
    return ' '.join(part for part in [company.strip(), query_suffix.strip()] if part).strip()


def normalize_keyword_terms(value: Any, query_suffix: str) -> list[str]:
    if isinstance(value, str):
        candidates = re.split(r',|\n', value)
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict, str)):
        candidates = [str(item) for item in value]
    else:
        candidates = []

    normalized = [candidate.strip().lower() for candidate in candidates if str(candidate).strip()]
    if normalized:
        return sorted(set(normalized))

    inferred_terms = re.findall(r'[A-Za-z][A-Za-z0-9\-]{1,}', query_suffix.lower())
    fallback_terms = DEFAULT_KEYWORD_TERMS + inferred_terms
    return sorted(set(fallback_terms))


def normalize_jina_engine(value: Any) -> str:
    engine = normalize_text(value, DEFAULT_JINA_ENGINE).lower()
    return engine if engine in ALLOWED_JINA_ENGINES else DEFAULT_JINA_ENGINE


def extract_url_strings(value: str) -> list[str]:
    stripped = value.strip()
    if stripped.startswith(('http://', 'https://')):
        return [stripped]
    return URL_PATTERN.findall(stripped)


def collect_link_candidates(value: Any, path: str = 'root') -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []

    if isinstance(value, dict):
        for key, nested_value in value.items():
            candidates.extend(collect_link_candidates(nested_value, f'{path}.{key}'))
        return candidates

    if isinstance(value, list):
        for index, nested_value in enumerate(value):
            candidates.extend(collect_link_candidates(nested_value, f'{path}[{index}]'))
        return candidates

    if isinstance(value, str):
        for url in extract_url_strings(value):
            candidates.append({'path': path, 'url': url})

    return candidates


def normalize_forward_url(raw_url: str) -> str | None:
    cleaned = raw_url.strip().rstrip('.,;:)')
    if not cleaned:
        return None

    parsed = urlparse(cleaned)
    if parsed.scheme not in {'http', 'https'}:
        return None

    if 'google.' in parsed.netloc.lower():
        query = parse_qs(parsed.query)
        for key in ('q', 'url'):
            for nested_url in query.get(key, []):
                normalized_nested = normalize_forward_url(unquote(nested_url))
                if normalized_nested:
                    return normalized_nested
        return None

    if not parsed.netloc:
        return None

    path_lower = parsed.path.lower()
    if any(path_lower.endswith(extension) for extension in SKIPPED_FILE_EXTENSIONS):
        return None

    sanitized = parsed._replace(fragment='')
    return urlunparse(sanitized)


def deduplicate_strings(values: Iterable[str]) -> list[str]:
    deduplicated: list[str] = []
    seen: set[str] = set()

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)

    return deduplicated


def collect_searchable_fragments(value: Any, fragments: list[str], max_fragments: int = 200) -> None:
    if len(fragments) >= max_fragments:
        return

    if isinstance(value, dict):
        for nested_value in value.values():
            collect_searchable_fragments(nested_value, fragments, max_fragments=max_fragments)
        return

    if isinstance(value, list):
        for nested_value in value:
            collect_searchable_fragments(nested_value, fragments, max_fragments=max_fragments)
        return

    if isinstance(value, str):
        text = value.strip()
        if text:
            fragments.append(text)


def build_searchable_text(value: Any) -> str:
    fragments: list[str] = []
    collect_searchable_fragments(value, fragments)
    return ' '.join(fragments).lower()


def annotate_crawler_items(items: list[dict[str, Any]], keyword_terms: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    annotated_items: list[dict[str, Any]] = []
    matched_items: list[dict[str, Any]] = []

    for item in items:
        searchable_text = build_searchable_text(item)
        matched_keywords = [term for term in keyword_terms if term in searchable_text]
        relevance = round(len(matched_keywords) / len(keyword_terms), 3) if keyword_terms else 0.0

        annotated_item = {
            **item,
            'analysis_matched_keywords': matched_keywords,
            'analysis_keyword_match_count': len(matched_keywords),
            'analysis_keyword_relevance': relevance,
        }
        annotated_items.append(annotated_item)

        if matched_keywords:
            matched_items.append(annotated_item)

    return annotated_items, matched_items


async def collect_dataset_items(dataset_id: str) -> list[dict[str, Any]]:
    dataset_items: list[dict[str, Any]] = []

    async for item in Actor.apify_client.dataset(dataset_id).iterate_items():
        if isinstance(item, dict):
            dataset_items.append(item)
        else:
            dataset_items.append({'value': item})

    return dataset_items
