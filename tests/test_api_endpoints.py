"""End-to-end integration tests for all ResearchPilot FastAPI endpoints.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.database import init_db


@pytest.mark.asyncio
async def test_full_api_workflow():
    init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health Root & Dashboard
        resp_html = await client.get("/")
        assert resp_html.status_code == 200
        assert "ResearchPilot" in resp_html.text

        resp_api = await client.get("/api")
        assert resp_api.status_code == 200
        assert resp_api.json()["status"] == "operational"

        # 2. Create Project
        proj_payload = {
            "name": "Cross-Dataset Robustness Evaluation",
            "topic": "Cross-dataset robustness of machine-learning methods for phishing detection",
            "year_range": "2018-2024"
        }
        resp = await client.post("/api/projects", json=proj_payload)
        assert resp.status_code == 201
        project_data = resp.json()
        project_id = project_data["id"]
        assert project_id.startswith("proj-")

        # 3. Analyze Scope
        scope_payload = {
            "topic": "Cross-dataset robustness of machine-learning methods for phishing detection"
        }
        resp = await client.post("/api/projects/analyze-scope", json=scope_payload)
        assert resp.status_code == 200
        scope_data = resp.json()
        assert len(scope_data["research_questions"]) == 3
        assert 0 <= scope_data["feasibility_score"] <= 100
        assert "openalex" in scope_data["boolean_queries"]

        # 4. Seed Corpus
        resp = await client.post(f"/api/projects/{project_id}/seed-corpus")
        assert resp.status_code == 200
        seed_data = resp.json()
        assert seed_data["status"] == "success"
        assert len(seed_data["papers"]) == 25
        assert seed_data["total_corpus_count"] >= 25

        # 5. Semantic Vector Search
        search_query = "adversarial attacks and concept drift in phishing detection"
        resp = await client.get(f"/api/projects/{project_id}/vector-search?q={search_query}&limit=5")
        assert resp.status_code == 200
        search_data = resp.json()
        assert len(search_data["papers"]) == 5
        assert search_data["papers"][0]["similarity_score"] >= search_data["papers"][1]["similarity_score"]

        # 6. Import BibTeX / DOI
        unique_doi = f"10.1109/ACCESS.2023.{uuid.uuid4().hex[:7]}"
        bib_payload = {
            "raw_content": unique_doi,
            "default_source": "DOI Manual"
        }
        resp = await client.post(f"/api/projects/{project_id}/import-bibtex", json=bib_payload)
        assert resp.status_code == 200
        import_data = resp.json()
        assert import_data["imported_count"] == 1

        # 7. System Diagnostics
        resp = await client.get("/api/system/diagnostics")
        assert resp.status_code == 200
        diag_data = resp.json()
        assert len(diag_data["providers"]) >= 4

        # 8. Simulate SSE Stream
        resp = await client.get("/api/runs/run-demo-1/simulate-sse")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        text = resp.text
        assert "simulation_mode" in text
        assert "Stage 1: Topic Scope Analyzer" in text
        assert "Stage 9: Meta-Reviewer & Report Generator" in text
