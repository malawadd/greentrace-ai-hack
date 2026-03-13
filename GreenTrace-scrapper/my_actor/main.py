"""Main entry point for the GreenTrace-scrapper Actor."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from apify import Actor

from .fast_crawler import FAST_CRAWLER_ACTOR_ID, run_fast_crawler
from .jina_ai import run_jina_reader
from .utils import (
    DEFAULT_COMPANY,
    DEFAULT_JINA_TIMEOUT_SECS,
    DEFAULT_QUERY_SUFFIX,
    build_query,
    coerce_bool,
    coerce_positive_int,
    collect_dataset_items,
    collect_link_candidates,
    deduplicate_strings,
    normalize_forward_url,
    normalize_jina_engine,
    normalize_keyword_terms,
    normalize_text,
    run_finished_successfully,
    status_to_string,
)

GOOGLE_SEARCH_ACTOR_ID = 'apify/google-search-scraper'


def _build_initial_summary(
    company: str,
    query: str,
    query_suffix: str,
    keyword_terms: list[str],
    results_per_page: int,
    max_pages_per_query: int,
    enable_fast_crawler: bool,
    enable_jina_ai: bool,
    jina_engine: str,
) -> dict[str, Any]:
    return {
        'company': company,
        'query': query,
        'query_suffix': query_suffix,
        'keyword_terms': keyword_terms,
        'results_per_page': results_per_page,
        'max_pages_per_query': max_pages_per_query,
        'enable_fast_crawler': enable_fast_crawler,
        'enable_jina_ai': enable_jina_ai,
        'jina_engine': jina_engine,
        'google_stage': {
            'status': 'pending',
            'actor_id': GOOGLE_SEARCH_ACTOR_ID,
            'run_id': None,
            'run_status': None,
            'status_message': None,
            'result_count': 0,
            'link_candidate_count': 0,
            'error': None,
        },
        'crawler_stage': {
            'status': 'disabled' if not enable_fast_crawler else 'pending',
            'actor_id': FAST_CRAWLER_ACTOR_ID,
            'run_id': None,
            'run_status': None,
            'status_message': 'Fast crawler disabled by input.' if not enable_fast_crawler else None,
            'result_count': 0,
            'matching_result_count': 0,
            'error': None,
        },
        'jina_stage': {
            'status': 'disabled' if not enable_jina_ai else 'pending',
            'provider': 'jina.ai',
            'engine': jina_engine,
            'attempted_count': 0,
            'success_count': 0,
            'failure_count': 0,
            'used_api_key': False,
            'error': None,
        },
        'google_results': [],
        'google_link_candidates': [],
        'forwarded_urls': [],
        'crawler_results': [],
        'matching_crawler_results': [],
        'jina_results': [],
        'overall_status': 'pending',
    }


def _finalize_overall_status(summary: dict[str, Any]) -> None:
    google_status = summary['google_stage']['status']
    crawler_status = summary['crawler_stage']['status']
    jina_status = summary['jina_stage']['status']

    non_terminal_success = {'succeeded', 'skipped', 'disabled'}

    if google_status == 'failed':
        summary['overall_status'] = 'failed'
        return

    if google_status == 'succeeded' and crawler_status in non_terminal_success and jina_status in non_terminal_success:
        summary['overall_status'] = 'succeeded'
        return

    summary['overall_status'] = 'partial'


async def _run_google_stage(summary: dict[str, Any], query: str, results_per_page: int, max_pages_per_query: int) -> None:
    google_run = await Actor.call(
        GOOGLE_SEARCH_ACTOR_ID,
        run_input={
            'queries': query,
            'resultsPerPage': results_per_page,
            'maxPagesPerQuery': max_pages_per_query,
        },
        wait=timedelta(minutes=15),
    )
    if google_run is None:
        raise RuntimeError('Google search actor did not return run metadata.')

    google_results = await collect_dataset_items(google_run.default_dataset_id)
    google_link_candidates = collect_link_candidates(google_results, 'google_results')
    google_run_status = status_to_string(google_run.status)
    forwarded_urls = deduplicate_strings(
        normalized_url
        for normalized_url in (normalize_forward_url(candidate['url']) for candidate in google_link_candidates)
        if normalized_url
    )

    summary['google_results'] = google_results
    summary['google_link_candidates'] = google_link_candidates
    summary['forwarded_urls'] = forwarded_urls
    summary['google_stage'].update(
        {
            'status': 'succeeded' if run_finished_successfully(google_run_status) else 'failed',
            'run_id': google_run.id,
            'run_status': google_run_status,
            'status_message': google_run.status_message,
            'result_count': len(google_results),
            'link_candidate_count': len(google_link_candidates),
            'error': None if run_finished_successfully(google_run_status) else google_run.status_message,
        }
    )


async def main() -> None:
    """Run Google search and optional downstream enrichment stages."""
    async with Actor:
        actor_input = await Actor.get_input() or {}

        company = normalize_text(actor_input.get('company'), DEFAULT_COMPANY)
        results_per_page = coerce_positive_int(actor_input.get('results_per_page'), 10)
        max_pages_per_query = coerce_positive_int(actor_input.get('max_pages_per_query'), 1)
        query_suffix = normalize_text(actor_input.get('query_suffix'), DEFAULT_QUERY_SUFFIX)
        keyword_terms = normalize_keyword_terms(actor_input.get('keyword_terms'), query_suffix)
        enable_fast_crawler = coerce_bool(actor_input.get('enable_fast_crawler'), False)
        enable_jina_ai = coerce_bool(actor_input.get('enable_jina_ai'), True)
        jina_api_key = normalize_text(actor_input.get('jina_api_key')) or None
        jina_engine = normalize_jina_engine(actor_input.get('jina_engine'))
        jina_timeout_secs = coerce_positive_int(actor_input.get('jina_timeout_secs'), DEFAULT_JINA_TIMEOUT_SECS)
        query = build_query(company, query_suffix)

        summary = _build_initial_summary(
            company=company,
            query=query,
            query_suffix=query_suffix,
            keyword_terms=keyword_terms,
            results_per_page=results_per_page,
            max_pages_per_query=max_pages_per_query,
            enable_fast_crawler=enable_fast_crawler,
            enable_jina_ai=enable_jina_ai,
            jina_engine=jina_engine,
        )

        Actor.log.info(f'Running Google ESG search for {company}: {query}')

        try:
            await _run_google_stage(summary, query, results_per_page, max_pages_per_query)
            Actor.log.info(
                f'Google stage finished with {len(summary["google_results"])} result items and '
                f'{len(summary["forwarded_urls"])} forwarded URLs.'
            )
        except Exception as exc:
            summary['google_stage'].update({'status': 'failed', 'error': str(exc)})
            Actor.log.exception('Google stage failed.')

        if summary['forwarded_urls']:
            if enable_fast_crawler:
                try:
                    Actor.log.info(
                        f'Forwarding {len(summary["forwarded_urls"])} URLs to {FAST_CRAWLER_ACTOR_ID}.'
                    )
                    crawler_payload = await run_fast_crawler(summary['forwarded_urls'], keyword_terms)
                    summary['crawler_stage'] = crawler_payload['stage']
                    summary['crawler_results'] = crawler_payload['crawler_results']
                    summary['matching_crawler_results'] = crawler_payload['matching_crawler_results']
                except Exception as exc:
                    summary['crawler_stage'].update({'status': 'failed', 'error': str(exc)})
                    Actor.log.exception('Crawler stage failed.')

            if enable_jina_ai:
                try:
                    Actor.log.info(
                        f'Fetching Jina reader content for {len(summary["forwarded_urls"])} forwarded URLs with engine {jina_engine}.'
                    )
                    jina_payload = await run_jina_reader(
                        summary['forwarded_urls'],
                        engine=jina_engine,
                        timeout_secs=jina_timeout_secs,
                        api_key=jina_api_key,
                    )
                    summary['jina_stage'] = jina_payload['stage']
                    summary['jina_results'] = jina_payload['jina_results']
                except Exception as exc:
                    summary['jina_stage'].update({'status': 'failed', 'error': str(exc)})
                    Actor.log.exception('Jina stage failed.')
        else:
            if enable_fast_crawler:
                summary['crawler_stage'].update(
                    {
                        'status': 'skipped',
                        'status_message': 'No crawlable URLs were produced by the Google stage.',
                    }
                )
            if enable_jina_ai:
                summary['jina_stage'].update(
                    {
                        'status': 'skipped',
                        'error': None,
                    }
                )

        _finalize_overall_status(summary)
        await Actor.push_data(summary)
