from __future__ import annotations

import asyncio
from typing import Any

import requests

JINA_READER_URL = 'https://r.jina.ai/'


def _fetch_single_jina_result(url: str, api_key: str | None, engine: str, timeout_secs: int) -> dict[str, Any]:
    headers = {
        'Content-Type': 'application/json',
        'X-Engine': engine,
        'X-Retain-Images': 'none',
        'X-Timeout': str(timeout_secs),
    }
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    response = requests.post(
        JINA_READER_URL,
        headers=headers,
        json={'url': url},
        timeout=max(timeout_secs, 30),
    )
    response.raise_for_status()

    return {
        'url': url,
        'engine': engine,
        'status_code': response.status_code,
        'content': response.text,
        'used_api_key': bool(api_key),
    }


async def run_jina_reader(
    forwarded_urls: list[str],
    engine: str,
    timeout_secs: int,
    api_key: str | None = None,
) -> dict[str, Any]:
    jina_results: list[dict[str, Any]] = []

    for url in forwarded_urls:
        try:
            result = await asyncio.to_thread(_fetch_single_jina_result, url, api_key, engine, timeout_secs)
            jina_results.append(result)
        except Exception as exc:
            jina_results.append(
                {
                    'url': url,
                    'engine': engine,
                    'content': None,
                    'used_api_key': bool(api_key),
                    'error': str(exc),
                }
            )

    success_count = sum(1 for item in jina_results if not item.get('error'))
    failure_count = len(jina_results) - success_count

    return {
        'stage': {
            'status': 'succeeded' if failure_count == 0 else ('failed' if success_count == 0 else 'partial'),
            'provider': 'jina.ai',
            'engine': engine,
            'attempted_count': len(jina_results),
            'success_count': success_count,
            'failure_count': failure_count,
            'used_api_key': bool(api_key),
            'error': None if success_count else 'Jina reader failed for all forwarded URLs.',
        },
        'jina_results': jina_results,
    }
