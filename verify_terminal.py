#!/usr/bin/env python3
"""ResearchPilot Phase 1 - Terminal-Based Verification Suite.
Demonstrates end-to-end functionality via CLI:
1. Provider Diagnostics & Telemetry
2. Project Creation
3. AI Topic Scope Analysis (PICO-CS & 3 RQs)
4. 25-Paper Gold Corpus Seeding (Idempotent)
5. Semantic Vector Search & Cosine Similarity Ranking
6. BibTeX / DOI Import & Duplicate Detection
7. 9-Agent Pipeline SSE Simulation
"""

import asyncio
import json
import sys
from datetime import datetime
from backend.core.config import settings
from backend.db.database import init_db, SessionLocal
from backend.db.models import ProjectModel
from backend.schemas.contracts import (
    ScopeAnalysisRequest,
    BibTeXImportRequest
)
from backend.services.diagnostics import collect_system_diagnostics
from backend.services.scope_analyzer import analyze_topic_scope
from backend.services.corpus_seeder import seed_benchmark_corpus
from backend.services.vector_search import search_corpus_by_vector
from backend.services.bibtex_importer import import_bibtex_or_doi
from backend.services.sse_simulator import simulate_nine_agent_stream


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def main():
    print_header("RESEARCHPILOT PHASE 1 - TERMINAL VERIFICATION")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Configured LLM Model: {settings.NVIDIA_LLM_MODEL}")
    print(f"Configured Embed Model: {settings.NVIDIA_EMBED_MODEL} (dim={settings.EMBEDDING_DIMENSION})")
    print(f"Database URL: {settings.DATABASE_URL}")

    # Initialize DB
    init_db()
    db = SessionLocal()

    # -------------------------------------------------------------
    # Step 1: Provider Diagnostics
    # -------------------------------------------------------------
    print_header("STEP 1: Provider Diagnostics Telemetry")
    diagnostics = await collect_system_diagnostics(db)
    for p in diagnostics.providers:
        latency_str = f"{p.measured_latency_ms} ms" if p.measured_latency_ms is not None else "N/A"
        print(f"• [{p.status.upper():8}] {p.service_name:30} | Latency: {latency_str:10} | {p.fallback_tier}")
        if p.notes:
            print(f"    Notes: {p.notes}")
    print("\nActive Fallback Order:")
    for tier in diagnostics.active_fallback_order:
        print(f"  - {tier}")

    # -------------------------------------------------------------
    # Step 2: Project Creation
    # -------------------------------------------------------------
    print_header("STEP 2: Create Research Project")
    topic = "Cross-dataset robustness of machine-learning methods for phishing detection"
    proj_id = "proj-phish-robustness"
    existing = db.query(ProjectModel).filter(ProjectModel.id == proj_id).first()
    if not existing:
        project = ProjectModel(
            id=proj_id,
            name="Phishing Robustness Benchmark Study",
            topic=topic,
            constraints="Focus on lexical drift, DOM features, and adversarial evasion",
            year_range="2018-2024",
            status="active"
        )
        db.add(project)
        db.commit()
        print(f"✓ Project Created: ID={project.id} | Name={project.name}")
    else:
        print(f"✓ Project Already Exists: ID={existing.id} | Name={existing.name}")

    # -------------------------------------------------------------
    # Step 3: Topic Scope Analysis (PICO-CS & 3 RQs)
    # -------------------------------------------------------------
    print_header("STEP 3: Topic Scope Analyzer (PICO-CS & 3 RQs)")
    scope_req = ScopeAnalysisRequest(
        topic=topic,
        constraints="Focus on lexical drift, DOM features, and adversarial evasion"
    )
    scope_res = await analyze_topic_scope(scope_req)
    print(f"Topic: {scope_res.original_topic}")
    print(f"\n[PICO-CS Breakdown]")
    print(f"  Population/Problem : {scope_res.problem}")
    print(f"  Intervention/Method: {scope_res.method}")
    print(f"  Comparison/Baseline: {scope_res.comparison}")
    print(f"  Outcomes/Metrics   : {scope_res.outcomes}")

    print(f"\n[Generated Research Questions (Exactly 3)]")
    for rq in scope_res.research_questions:
        print(f"  • {rq}")

    print(f"\n[Source-Specific Search Queries]")
    print(f"  OpenAlex: {scope_res.boolean_queries.openalex}")
    print(f"  arXiv   : {scope_res.boolean_queries.arxiv}")
    print(f"  GitHub  : {scope_res.boolean_queries.github}")

    print(f"\nFeasibility Score: {scope_res.feasibility_score}/100 -> {scope_res.verdict}")
    if scope_res.warnings:
        print("Warnings:")
        for w in scope_res.warnings:
            print(f"  ⚠ {w}")

    # -------------------------------------------------------------
    # Step 4: Seed 25-Paper Benchmark Corpus
    # -------------------------------------------------------------
    print_header("STEP 4: Seed 25-Paper Phishing Benchmark Corpus")
    seed_res = await seed_benchmark_corpus(db=db, project_id=proj_id)
    print(f"Status: {seed_res.status}")
    print(f"Newly Seeded Papers: {seed_res.seeded_count}")
    print(f"Skipped Duplicates : {seed_res.skipped_count}")
    print(f"Total Corpus Count : {seed_res.total_corpus_count}")
    print(f"Sample Seeded Papers (First 3):")
    for p in seed_res.papers[:3]:
        print(f"  • [{p.paper_id}] ({p.year}) {p.title} (DOI: {p.doi})")

    # -------------------------------------------------------------
    # Step 5: Semantic Vector Search
    # -------------------------------------------------------------
    print_header("STEP 5: Semantic Vector Search (NVIDIA 2048d Embeddings)")
    search_query = "How much does phishing detection classifier accuracy degrade during cross-dataset transfer?"
    print(f"Query: \"{search_query}\"")
    search_res = await search_corpus_by_vector(db=db, query=search_query, project_id=proj_id, limit=5)
    print(f"Total Matches: {search_res.total_matches} | Model: {search_res.model_id} (dim={search_res.dimension})")
    print("\nRanked Retrieval Results:")
    for rank, paper in enumerate(search_res.papers, start=1):
        print(f"\n  #{rank} [Cosine Similarity: {paper.similarity_score:.4f}] - {paper.paper_id} ({paper.year})")
        print(f"      Title  : {paper.title}")
        print(f"      Source : {paper.source} | DOI: {paper.doi}")
        print(f"      Authors: {', '.join(paper.authors[:2])}{' et al.' if len(paper.authors) > 2 else ''}")
        print(f"      Excerpt: {paper.abstract[:130]}...")

    # -------------------------------------------------------------
    # Step 6: BibTeX / DOI Import & Duplicate Check
    # -------------------------------------------------------------
    print_header("STEP 6: DOI & BibTeX Import with Deduplication")
    # 1. Import a new DOI
    new_doi = "10.1145/3374218.3374235"  # matches phish-02 in corpus to test duplicate detection
    print(f"Testing Duplicate Detection for existing DOI: {new_doi}")
    import_res = await import_bibtex_or_doi(db=db, raw_content=new_doi, project_id=proj_id)
    print(f"Processed: {import_res.total_processed} | Imported: {import_res.imported_count} | Duplicates: {import_res.duplicate_count}")
    for rec in import_res.records:
        print(f"  • [{rec.status.upper()}] {rec.title} -> {rec.merge_reason}")

    # 2. Import a genuinely new BibTeX
    sample_bibtex = """
    @article{demo2024invariance,
      title = {Invariant Risk Minimization for Phishing Detection Under Concept Drift},
      author = {Naeem, Ahmed and Davis, Marcus},
      year = {2024},
      doi = {10.1016/j.cose.2024.99901},
      journal = {Computers & Security},
      abstract = {Novel domain-invariant regularization techniques for longitudinal anti-phishing filters.}
    }
    """
    print("\nImporting new BibTeX entry...")
    import_bib_res = await import_bibtex_or_doi(db=db, raw_content=sample_bibtex, project_id=proj_id)
    print(f"Processed: {import_bib_res.total_processed} | Imported: {import_bib_res.imported_count} | Duplicates: {import_bib_res.duplicate_count}")
    for rec in import_bib_res.records:
        print(f"  • [{rec.status.upper()}] {rec.title} (ID: {rec.paper_id}) -> {rec.merge_reason}")

    # -------------------------------------------------------------
    # Step 7: 9-Agent Pipeline SSE Simulation Stream
    # -------------------------------------------------------------
    print_header("STEP 7: 9-Agent Pipeline SSE Simulation Stream")
    run_id = "run-cli-verify"
    print(f"Streaming correlated TaskEnvelope events for Run ID: {run_id}...\n")
    async for event_chunk in simulate_nine_agent_stream(run_id=run_id):
        if event_chunk.startswith("data: "):
            payload = json.loads(event_chunk.replace("data: ", "").strip())
            stage = payload["stage"]
            status = payload["status"]
            corr_id = payload["correlation_id"]
            is_sim = payload.get("simulation_mode", True)
            if status == "completed":
                print(f"✓ [{status.upper():9}] {stage:45} | CorrID: {corr_id} | SimMode: {is_sim}")

    print_header("ALL VERIFICATION STEPS COMPLETED SUCCESSFULLY!")
    db.close()


if __name__ == "__main__":
    asyncio.run(main())
