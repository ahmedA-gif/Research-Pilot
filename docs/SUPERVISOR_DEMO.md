# ResearchPilot — Supervisor Demo Script (5-7 Minutes)

This script guides the supervisor demonstration showing that Week 1 is reproducible, measurable, and transparent about implemented versus simulated capabilities.

---

### Step 1: Provider Diagnostics & Health Telemetry (1 Minute)
1. Run:
   ```bash
   .venv/bin/python verify_terminal.py
   ```
2. **What to show**:
   - Inspect the live provider status table:
     - Database persistence layer (PostgreSQL or local vector store).
     - NVIDIA NIM Chat LLM (`nvidia/nemotron-3-super-120b-a12b`).
     - NVIDIA NIM Embeddings (`nvidia/nemotron-3.5-embed-1b`, 2048 dimensions).
     - External Scholarly APIs (OpenAlex, arXiv, GitHub Search).
   - Point out latency measurements in milliseconds.
   - Show the transparent fallback order: when an API key is absent or a provider fails, the system safely falls back to deterministic mock mode without crashing or faking live generation.

---

### Step 2: Project Creation & Topic Scope Analyzer (2 Minutes)
1. Topic used:
   `"Cross-dataset robustness of machine-learning methods for phishing detection"`
2. **What to show**:
   - **PICO-CS Breakdown**:
     - *Population/Problem*: Degradation of classifiers under non-stationary dataset drift.
     - *Intervention/Method*: Multi-modal alignment, invariant risk minimization.
     - *Comparison*: Static k-fold splits, baseline decision tree ensembles.
     - *Outcomes*: Cross-dataset transfer metrics, adversarial evasion resistance.
   - **Three Research Questions (RQs)**:
     - RQ1 on lexical vs. DOM distribution drift degradation.
     - RQ2 on invariant feature subsets across feeds (PhishTank to telemetry).
     - RQ3 on multi-modal graph robustness against homoglyph & path padding evasion attacks.
   - **Search Queries**:
     - Ready-to-run queries generated for OpenAlex, arXiv, and GitHub.
   - **Feasibility Gauge**:
     - Score (88/100) and actionable warnings (e.g., ensuring temporal splitting instead of random k-fold).

---

### Step 3: 25-Paper Gold Corpus & Semantic Vector Search (2 Minutes)
1. **What to show**:
   - The 25-paper benchmark corpus seeded idempotently into the database.
   - Re-running the seeder skips existing records without duplicating data.
   - Execute query:
     `"How much does phishing detection classifier accuracy degrade during cross-dataset transfer?"`
   - Show ranked results with cosine similarity scores, publication years, DOIs, authors, and abstract excerpts.
   - Reference the 10 Gold Q&A acceptance cases in `data/gold_qa_10.json`.

---

### Step 4: DOI & BibTeX Importer with Duplicate Detection (1 Minute)
1. **What to show**:
   - Test duplicate detection by importing DOI `10.1145/3374218.3374235` (already present). System detects duplicate and cites merge reason.
   - Import a new BibTeX record: parses fields, normalizes DOI, computes passage embedding, and persists with audit log.

---

### Step 5: 9-Agent Pipeline SSE Simulation Stream (1 Minute)
1. **What to show**:
   - Stream of all 9 agent stages over Server-Sent Events (SSE).
   - Point out correlated `run_id` and `correlation_id` across events.
   - **Transparency disclosure**: Emphasize that in Week 1, the 9-stage handoff is in contract simulation mode (`simulation_mode=True`) validating payloads before full LangGraph agent orchestration in subsequent phases.
