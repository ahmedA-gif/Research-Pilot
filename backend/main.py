"""ResearchPilot Backend Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.db.database import init_db
from backend.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook: initialize database tables on startup."""
    init_db()
    yield


# Initialize database tables on startup
init_db()

app = FastAPI(
    title="ResearchPilot API",
    version="1.0.0",
    description="ResearchPilot Week 1 Foundation - Scope Analysis, pgvector Search & 9-Agent Simulator",
    lifespan=lifespan
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ResearchPilot Core API",
        "phase": "Week 1 - Foundation, Contracts & First Visible Win",
        "status": "operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "create_project": "POST /api/projects",
            "analyze_scope": "POST /api/projects/analyze-scope",
            "seed_corpus": "POST /api/projects/{id}/seed-corpus",
            "vector_search": "GET /api/projects/{id}/vector-search?q=...",
            "import_bibtex": "POST /api/projects/{id}/import-bibtex",
            "diagnostics": "GET /api/system/diagnostics",
            "simulate_sse": "GET /api/runs/{id}/simulate-sse"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
