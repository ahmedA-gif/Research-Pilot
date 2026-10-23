"""FastAPI routing table implementing all required Week 1 endpoints.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import ProjectModel
from backend.schemas.contracts import (
    Project,
    ProjectCreate,
    ScopeAnalysisRequest,
    ScopeAnalysisResult,
    CorpusSeedResponse,
    VectorSearchResponse,
    BibTeXImportRequest,
    BibTeXImportResponse,
    SystemDiagnosticsReport
)
from backend.services.scope_analyzer import analyze_topic_scope
from backend.services.corpus_seeder import seed_benchmark_corpus
from backend.services.vector_search import search_corpus_by_vector
from backend.services.bibtex_importer import import_bibtex_or_doi
from backend.services.diagnostics import collect_system_diagnostics
from backend.services.sse_simulator import simulate_nine_agent_stream

router = APIRouter(prefix="/api", tags=["ResearchPilot Phase 1"])


# ---------------------------------------------------------
# 1. Project Management
# ---------------------------------------------------------

@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new research project workspace."""
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    project = ProjectModel(
        id=project_id,
        name=payload.name,
        topic=payload.topic,
        constraints=payload.constraints,
        year_range=payload.year_range or "2018-2024",
        status="active"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Fetch project details by ID."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return project


# ---------------------------------------------------------
# 2. Topic Scope Analysis (PICO-CS & RQs)
# ---------------------------------------------------------

@router.post("/projects/analyze-scope", response_model=ScopeAnalysisResult)
async def analyze_scope(payload: ScopeAnalysisRequest):
    """Decompose research topic into PICO-CS, generate 3 RQs and query strings."""
    try:
        return await analyze_topic_scope(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scope analysis failed: {str(e)}"
        )


# ---------------------------------------------------------
# 3. Benchmark Corpus Seeder
# ---------------------------------------------------------

@router.post("/projects/{project_id}/seed-corpus", response_model=CorpusSeedResponse)
async def seed_corpus(project_id: str, db: Session = Depends(get_db)):
    """Idempotently seed the 25 curated papers with 2048-dim passage embeddings."""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        # Auto-create if project does not exist yet for rapid demo convenience
        project = ProjectModel(
            id=project_id,
            name=f"Demo Project ({project_id})",
            topic="cross-dataset robustness of machine-learning methods for phishing detection"
        )
        db.add(project)
        db.commit()

    try:
        return await seed_benchmark_corpus(db=db, project_id=project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed corpus: {str(e)}"
        )


# ---------------------------------------------------------
# 4. Semantic Vector Search
# ---------------------------------------------------------

@router.get("/projects/{project_id}/vector-search", response_model=VectorSearchResponse)
async def vector_search(
    project_id: str,
    q: str = Query(..., min_length=2, description="Semantic search query"),
    limit: int = Query(10, ge=1, le=25),
    db: Session = Depends(get_db)
):
    """Rank stored paper embeddings using cosine similarity against the query embedding."""
    try:
        return await search_corpus_by_vector(db=db, query=q, project_id=project_id, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search execution error: {str(e)}"
        )


# ---------------------------------------------------------
# 5. BibTeX and DOI Import
# ---------------------------------------------------------

@router.post("/projects/{project_id}/import-bibtex", response_model=BibTeXImportResponse)
async def import_bibtex(
    project_id: str,
    payload: BibTeXImportRequest,
    db: Session = Depends(get_db)
):
    """Import and validate raw BibTeX entries or DOIs with duplicate detection."""
    try:
        return await import_bibtex_or_doi(
            db=db,
            raw_content=payload.raw_content,
            project_id=project_id,
            default_source=payload.default_source or "Manual Import"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import BibTeX/DOI records: {str(e)}"
        )


# ---------------------------------------------------------
# 6. Provider Diagnostics Telemetry
# ---------------------------------------------------------

@router.get("/system/diagnostics", response_model=SystemDiagnosticsReport)
async def get_system_diagnostics(db: Session = Depends(get_db)):
    """Fetch live system diagnostics, provider health, latency, and fallback tiers."""
    return await collect_system_diagnostics(db=db)


# ---------------------------------------------------------
# 7. 9-Agent SSE Pipeline Simulation Stream
# ---------------------------------------------------------

@router.get("/runs/{run_id}/simulate-sse")
async def simulate_pipeline_run(run_id: str):
    """Stream correlated TaskEnvelope payloads for all 9 agent handoff stages over SSE."""
    return StreamingResponse(
        simulate_nine_agent_stream(run_id=run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
