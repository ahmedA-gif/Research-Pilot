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


from pathlib import Path
from fastapi.responses import HTMLResponse

STATIC_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    """Serve the interactive ResearchPilot web dashboard."""
    if STATIC_INDEX.exists():
        with open(STATIC_INDEX, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>ResearchPilot API Operational</h1><p>Visit <a href='/docs'>/docs</a> for Swagger documentation.</p>")


@app.get("/api", tags=["Health"])
async def api_sitemap():
    """API health and sitemap."""
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
