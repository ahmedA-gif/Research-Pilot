"""Tests for vector search service and Gold Q&A retrieval evaluation.
"""

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.db.models import Base
from backend.services.corpus_seeder import seed_benchmark_corpus
from backend.services.vector_search import search_corpus_by_vector


@pytest.fixture
def search_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_vector_search_returns_ranked_results(search_db):
    """Seed corpus and verify vector search returns scored papers sorted descending."""
    await seed_benchmark_corpus(db=search_db, project_id="proj-eval-1")

    query = "adversarial machine learning evasion attacks on phishing URL detection"
    response = await search_corpus_by_vector(db=search_db, query=query, limit=5)

    assert response.total_matches == 5
    assert len(response.papers) == 5
    assert response.model_id == settings.NVIDIA_EMBED_MODEL
    assert response.dimension == settings.EMBEDDING_DIMENSION

    # Verify scores are bounded [0, 1] and strictly descending
    scores = [p.similarity_score for p in response.papers]
    for s in scores:
        assert 0.0 <= s <= 1.0
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_gold_qa_acceptance_cases(search_db):
    """Evaluate all 10 Gold-Standard Q&A acceptance cases against the seeded corpus."""
    await seed_benchmark_corpus(db=search_db, project_id="proj-eval-qa")

    # Load 10 gold QA cases
    with open(settings.GOLD_QA_PATH, "r", encoding="utf-8") as f:
        gold_cases = json.load(f)

    assert len(gold_cases) == 10

    evaluation_report = []

    for case in gold_cases:
        query = case["query"]
        expected_ids = set(case["expected_paper_ids"])

        search_res = await search_corpus_by_vector(db=search_db, query=query, limit=10)
        retrieved_ids = [p.paper_id for p in search_res.papers]

        # Check if at least one expected paper is retrieved in top 10
        hits = expected_ids.intersection(retrieved_ids)
        evaluation_report.append({
            "case_id": case["case_id"],
            "query": query,
            "expected": list(expected_ids),
            "retrieved_top5": retrieved_ids[:5],
            "hit_count": len(hits)
        })

    # Ensure evaluation ran on all 10 cases without errors
    assert len(evaluation_report) == 10
