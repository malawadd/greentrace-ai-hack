from pydantic import BaseModel, Field


class CompanyEsgOptions(BaseModel):
    query_suffix: str = "ESG sustainability greenwashing 2024 2025"
    results_per_page: int = Field(default=10, ge=1, le=100)
    max_pages_per_query: int = Field(default=1, ge=1, le=10)
    keyword_terms: list[str] | None = None
    enable_fast_crawler: bool = False
    enable_jina_ai: bool = True
    jina_api_key: str | None = None
    jina_engine: str = Field(default="direct", pattern="^(direct|browser)$")
    jina_timeout_secs: int = Field(default=200, ge=1, le=600)


class ArticleResult(BaseModel):
    title: str | None = None
    url: str
    content: str
    source: str


class CompanyEsgResponse(BaseModel):
    company: str
    overall_status: str = "unknown"
    article_count: int
    articles: list[ArticleResult]