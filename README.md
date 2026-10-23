# Research-Pilot

> **Phase 1 · Week 1 Implementation: Foundation, Contracts & The First Visible Win**

ResearchPilot is an autonomous AI scientific research assistant designed to scope complex scientific topics, formulate rigorous research questions, index scholarly literature with dense semantic vector representations, and orchestrate specialized multi-agent research pipelines.

---

## 🎯 Week 1 Delivery Summary

| Success Metric | Target | Status |
| :--- | :--- | :--- |
| **Curated Benchmark Papers** | 25 Genuine Open-Access Papers | ✅ **25 Papers Curated** (`data/seed_papers_25.json`) |
| **Gold Acceptance Cases** | 10 Evaluation Target Cases | ✅ **10 Gold Q&A Cases** (`data/gold_qa_10.json`) |
| **Embedding Dimensions** | 2,048 Dimensions | ✅ **NVIDIA Nemotron 3.5 Embed 1B** (`nvidia/nemotron-3.5-embed-1b`) |
| **LLM Reasoning Model** | NVIDIA Nemotron 3 Super | ✅ **NVIDIA Nemotron 3 Super 120B** (`nvidia/nemotron-3-super-120b-a12b`) |
| **Agent Handoff Pipeline** | 9-Stage Correlated Flow | ✅ **TaskEnvelope SSE Stream** (`simulation_mode=True`) |
| **Pydantic Data Contracts** | Strict Schema Validation | ✅ **11 Locked Data Contracts** (`backend/schemas/contracts.py`) |
| **Test Suite Coverage** | Unit, Idempotency & API tests | ✅ **23 / 23 Tests Passing** (`tests/`) |

---

## 🏗️ Repository Layout

```
ResearchPilot/
├── backend/
│   ├── api/routes.py            # FastAPI endpoints (Projects, Scope, Seed, Search, Import, SSE)
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment variable configuration
│   │   └── nvidia_client.py     # NVIDIA NIM HTTP client (LLM & Embeddings + deterministic mock)
│   ├── db/
│   │   ├── database.py          # SQLAlchemy engine, session maker & bootstrap
│   │   └── models.py            # Project, Paper, ImportAudit & RunEvent ORM models
│   ├── schemas/contracts.py     # Locked Pydantic v2 data contracts
│   ├── services/
│   │   ├── scope_analyzer.py    # PICO-CS breakdown & 3 research question generation
│   │   ├── corpus_seeder.py     # Idempotent seeder for 25-paper corpus
│   │   ├── embeddings.py        # 2048d passage/query embedding service & cosine similarity
│   │   ├── vector_search.py     # Cosine distance ranking search engine
│   │   ├── bibtex_importer.py   # DOI/BibTeX parser with normalization & duplicate check
│   │   ├── diagnostics.py       # Live telemetry for NVIDIA, DB, OpenAlex, arXiv, GitHub
│   │   └── sse_simulator.py     # 9-stage agent handoff Server-Sent Events simulator
│   └── main.py                  # FastAPI application entry point
├── frontend/
│   └── src/types/contracts.ts   # Synchronized TypeScript interfaces for Phase 1 & 2
├── data/
│   ├── seed_papers_25.json      # 25 curated genuine open-access phishing research papers
│   └── gold_qa_10.json          # 10 gold-standard Q&A acceptance cases
├── docs/
│   ├── ARCHITECTURE.md          # Architecture overview & mermaid data flow
│   ├── SUPERVISOR_DEMO.md       # 5-7 minute supervisor demonstration guide
│   └── GOLD_CORPUS_CHECKLIST.md # Corpus provenance & evaluation targets
├── tests/                       # Full pytest test suite (23 passing tests)
├── verify_terminal.py           # End-to-end terminal-based CLI verification script
├── docker-compose.yml           # PostgreSQL 16 + pgvector container configuration
├── pytest.ini                   # Pytest test configuration
├── .env.example                 # Environment variable template
└── README.md                    # Project documentation
```

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Git
- Optional: Docker (for PostgreSQL 16 + pgvector; SQLite is supported by default for quick local dev)

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional: Set your `NVIDIA_API_KEY` in `.env` to connect to live NVIDIA NIM endpoints; if omitted, the application operates in safe deterministic mock mode).*

### 4. Run the Test Suite (23 Tests)
```bash
pytest tests/ -v
```

### 5. Run the Terminal-Based Verification Script
Demonstrates all 7 components from the CLI:
```bash
python3 verify_terminal.py
```

### 6. Start the FastAPI Development Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at: `http://localhost:8000/docs`

---

## 📡 Required API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/projects` | Create a new research project workspace |
| `POST` | `/api/projects/analyze-scope` | Decompose raw topic into PICO-CS & 3 research questions |
| `POST` | `/api/projects/{id}/seed-corpus` | Idempotently seed 25 curated papers with 2048d embeddings |
| `GET` | `/api/projects/{id}/vector-search?q=...` | Rank stored papers using cosine similarity in query mode |
| `POST` | `/api/projects/{id}/import-bibtex` | Import & validate raw BibTeX/DOI with duplicate detection |
| `GET` | `/api/system/diagnostics` | System diagnostics & telemetry for NVIDIA, DB & scholarly APIs |
| `GET` | `/api/runs/{id}/simulate-sse` | Stream 9-stage pipeline handoff events over SSE (`TaskEnvelope`) |

---

## 🛡️ License & Team
Developed for **ResearchPilot** by the engineering team (Ahmed Naeem, Sameed, Umer).
