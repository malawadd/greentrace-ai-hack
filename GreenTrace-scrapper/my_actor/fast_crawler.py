from __future__ import annotations

from datetime import timedelta
from typing import Any

from apify import Actor

from .utils import annotate_crawler_items, collect_dataset_items, run_finished_successfully, status_to_string

FAST_CRAWLER_ACTOR_ID = '6sigmag/fast-website-content-crawler'


async def run_fast_crawler(forwarded_urls: list[str], keyword_terms: list[str]) -> dict[str, Any]:
    crawler_run = await Actor.call(
        FAST_CRAWLER_ACTOR_ID,
        run_input={'startUrls': forwarded_urls},
        wait=timedelta(minutes=15),
    )
    if crawler_run is None:
        raise RuntimeError('Fast website content crawler did not return run metadata.')

    crawler_results = await collect_dataset_items(crawler_run.default_dataset_id)
    crawler_run_status = status_to_string(crawler_run.status)
    annotated_crawler_results, matching_crawler_results = annotate_crawler_items(crawler_results, keyword_terms)

    return {
        'stage': {
            'status': 'succeeded' if run_finished_successfully(crawler_run_status) else 'failed',
            'actor_id': FAST_CRAWLER_ACTOR_ID,
            'run_id': crawler_run.id,
            'run_status': crawler_run_status,
            'status_message': crawler_run.status_message,
            'result_count': len(annotated_crawler_results),
            'matching_result_count': len(matching_crawler_results),
            'error': None if run_finished_successfully(crawler_run_status) else crawler_run.status_message,
        },
        'crawler_results': annotated_crawler_results,
        'matching_crawler_results': matching_crawler_results,
    }
