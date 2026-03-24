from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    url: str
    max_pages: Optional[int] = 50
    include_subdomains: bool = False


class TechnicalInsightRequest(BaseModel):
    url: str
    technical: dict[str, Any] = Field(default_factory=dict)


class SEOIssue(BaseModel):
    severity: str  # critical | warning | info
    category: str
    description: str
    affected_urls: list[str]
    recommendation: str


class CrawledPage(BaseModel):
    url: str
    status_code: int = 0
    response_time_ms: int = 0
    redirect_chain: list[str] = Field(default_factory=list)
    final_url: str = ""
    html_content: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    depth: int = 0
    error: Optional[str] = None


class TechnicalSEOResult(BaseModel):
    score: int
    https_status: dict[str, Any]
    page_speed: dict[str, Any]
    broken_links: list[str]
    redirect_chains: list[dict[str, Any]]
    canonical_issues: list[SEOIssue]
    robots_txt: dict[str, Any]
    sitemap: dict[str, Any]
    mobile_ready: bool
    critical_issues: list[SEOIssue]


class OnPageSEOResult(BaseModel):
    score: int
    missing_titles: int
    duplicate_titles: list[str]
    missing_metas: int
    duplicate_metas: list[str]
    thin_content_pages: list[str]
    missing_alt_count: int
    h1_issues: list[SEOIssue]
    avg_keyword_density: float
    top_keywords: list[dict[str, Any]]
    internal_linking_issues: list[SEOIssue]


class SemanticSEOResult(BaseModel):
    score: int
    top_entities: list[str]
    topic_clusters: list[dict[str, Any]]
    content_gaps: list[str]
    no_schema_pages: list[str]
    lsi_keywords: list[str]
    faq_opportunities: list[str]
    topical_authority_score: float


class UXSignalsResult(BaseModel):
    score: int
    avg_readability: float
    fk_grade: float
    pages_with_cta: float
    navigation_score: int
    content_structure_score: int


class AnalysisResult(BaseModel):
    analysis_id: str
    url: str
    created_at: str
    technical: dict[str, Any]
    onpage: dict[str, Any]
    semantic: dict[str, Any]
    ux: dict[str, Any]
    ai_analysis: str
    action_plan: list[dict[str, Any]]
