"""Pydantic v2 schemas and contracts for ResearchPilot.
Freezes data contracts for Phase 1 and future multi-agent pipelines.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# Core Project & Paper Contracts
# ---------------------------------------------------------

class Project(BaseModel):
    id: str
    name: str
    topic: str
    constraints: Optional[str] = None
    year_range: Optional[str] = "2018-2024"
    created_at: datetime = Field(default_factory=utc_now)
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    topic: str = Field(..., min_length=10, max_length=500)
    constraints: Optional[str] = None
    year_range: Optional[str] = "2018-2024"


class PaperRecord(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    source: Optional[str] = None
    abstract: str
    open_access_url: Optional[str] = None
    embedding_model: Optional[str] = "nvidia/nemotron-3.5-embed-1b"
    embedding_version: Optional[str] = "1.0"

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Scope Analysis & PICO-CS Contracts
# ---------------------------------------------------------

class ScopeAnalysisRequest(BaseModel):
    topic: str = Field(..., min_length=10, description="Raw research topic string")
    constraints: Optional[str] = Field(None, description="Optional boundaries or focus areas")


class BooleanQueries(BaseModel):
    openalex: str
    arxiv: str
    github: str


class ScopeAnalysisResult(BaseModel):
    original_topic: str
    problem: str
    method: str
    comparison: str
    outcomes: str
    research_questions: List[str] = Field(
        ...,
        description="Exactly three research questions generated from topic decomposition"
    )
    boolean_queries: BooleanQueries
    feasibility_score: int = Field(..., ge=0, le=100)
    verdict: str
    warnings: List[str] = Field(default_factory=list)
    is_mock: bool = False

    @field_validator("research_questions")
    @classmethod
    def validate_three_rqs(cls, v: List[str]) -> List[str]:
        if len(v) != 3:
            raise ValueError(f"Expected exactly 3 research questions, received {len(v)}")
        for rq in v:
            if not rq or len(rq.strip()) < 10:
                raise ValueError("Research question must be a non-trivial descriptive question")
        return v


# ---------------------------------------------------------
# Vector Search & Corpus Seed Contracts
# ---------------------------------------------------------

class ScoredPaper(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    source: Optional[str] = None
    abstract: str
    open_access_url: Optional[str] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class VectorSearchResponse(BaseModel):
    query: str
    total_matches: int
    papers: List[ScoredPaper]
    model_id: str
    dimension: int


class CorpusSeedResponse(BaseModel):
    status: str
    seeded_count: int
    skipped_count: int
    total_corpus_count: int
    papers: List[PaperRecord]


# ---------------------------------------------------------
# BibTeX / DOI Import Contracts
# ---------------------------------------------------------

class BibTeXImportRequest(BaseModel):
    raw_content: str = Field(..., min_length=3, description="BibTeX string or raw DOI")
    default_source: Optional[str] = "Manual Import"


class ImportedRecord(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    source: Optional[str] = None
    abstract: str
    status: str  # imported, duplicate, rejected
    merge_reason: Optional[str] = None


class BibTeXImportResponse(BaseModel):
    total_processed: int
    imported_count: int
    duplicate_count: int
    rejected_count: int
    records: List[ImportedRecord]


# ---------------------------------------------------------
# Provider Diagnostics Telemetry Contracts
# ---------------------------------------------------------

class ProviderDiagnosticItem(BaseModel):
    service_name: str
    configured: bool
    status: str  # online, degraded, offline, mock
    measured_latency_ms: Optional[float] = None
    fallback_tier: str
    model_id: Optional[str] = None
    notes: Optional[str] = None


class SystemDiagnosticsReport(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    providers: List[ProviderDiagnosticItem]
    active_fallback_order: List[str]
    cache_hit_ratio: float = 0.0


# ---------------------------------------------------------
# 9-Agent Pipeline & TaskEnvelope Contracts
# ---------------------------------------------------------

class TaskEnvelope(BaseModel):
    run_id: str
    correlation_id: str
    task_id: str
    stage: str
    status: str  # pending, running, completed, failed
    timestamp: datetime = Field(default_factory=utc_now)
    payload: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    simulation_mode: bool = True


# ---------------------------------------------------------
# Future Work Contracts (Locked for Week 1)
# ---------------------------------------------------------

class EvidenceSpan(BaseModel):
    span_id: str
    paper_id: str
    quote: str
    section: Optional[str] = None
    page: Optional[int] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class PaperProfile(BaseModel):
    paper_id: str
    primary_methods: List[str]
    datasets_used: List[str]
    findings: List[str]
    limitations: List[str]


class ResourceRecord(BaseModel):
    id: str
    name: str
    type: str  # code, dataset, benchmark, model
    url: Optional[str] = None
    description: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: Optional[float] = 1.0


class CandidateGap(BaseModel):
    id: str
    title: str
    description: str
    reason: str
    priority: str = "medium"  # high, medium, low


class ExperimentPlan(BaseModel):
    id: str
    title: str
    hypothesis: str
    methodology: str
    evaluation_metrics: List[str]


class VerificationAudit(BaseModel):
    audit_id: str
    status: str  # passed, warning, failed
    checks: List[Dict[str, Any]]
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
