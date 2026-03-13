from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.schemas.company_esg import CompanyEsgOptions, CompanyEsgResponse
from app.services.article_mapper import build_company_response
from app.services.greentrace_actor import ActorServiceError, run_greentrace_actor


router = APIRouter(tags=["green-trace"])


def build_options(
    query_suffix: Annotated[str, Query()] = "ESG sustainability greenwashing 2024 2025",
    results_per_page: Annotated[int, Query(ge=1, le=100)] = 10,
    max_pages_per_query: Annotated[int, Query(ge=1, le=10)] = 1,
    enable_fast_crawler: bool = False,
    enable_jina_ai: bool = True,
    jina_api_key: str | None = None,
    jina_engine: Annotated[str, Query(pattern="^(direct|browser)$")] = "direct",
    jina_timeout_secs: Annotated[int, Query(ge=1, le=600)] = 200,
    keyword_terms: list[str] | None = Query(default=None),
) -> CompanyEsgOptions:
    return CompanyEsgOptions(
        query_suffix=query_suffix,
        results_per_page=results_per_page,
        max_pages_per_query=max_pages_per_query,
        enable_fast_crawler=enable_fast_crawler,
        enable_jina_ai=enable_jina_ai,
        jina_api_key=jina_api_key,
        jina_engine=jina_engine,
        jina_timeout_secs=jina_timeout_secs,
        keyword_terms=keyword_terms,
    )


@router.get("/company-esg/{company}", response_model=CompanyEsgResponse)
def get_company_esg(
    company: Annotated[str, Path(min_length=1, max_length=200)],
    options: Annotated[CompanyEsgOptions, Depends(build_options)],
) -> CompanyEsgResponse:
    try:
        payload = run_greentrace_actor(company=company, options=options)
    except ActorServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return build_company_response(company=company, payload=payload)