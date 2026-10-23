"""Tests for corpus seeder service and idempotency.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, PaperModel
from backend.services.corpus_seeder import seed_benchmark_corpus


@pytest.fixture
def seeder_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_seeder_loads_all_25_papers_idempotently(seeder_db):
    """Verify first run seeds 25 papers; second run adds 0 duplicates."""
    # 1. First Run: Seed 25 papers
    res1 = await seed_benchmark_corpus(db=seeder_db, project_id="proj-demo-1")
    assert res1.status == "success"
    assert res1.seeded_count == 25
    assert res1.skipped_count == 0
    assert res1.total_corpus_count == 25

    count_after_first = seeder_db.query(PaperModel).count()
    assert count_after_first == 25

    # 2. Second Run: Re-seed identical corpus
    res2 = await seed_benchmark_corpus(db=seeder_db, project_id="proj-demo-1")
    assert res2.status == "success"
    assert res2.seeded_count == 0
    assert res2.skipped_count == 25
    assert res2.total_corpus_count == 25

    # Verify no duplicate entries were added
    count_after_second = seeder_db.query(PaperModel).count()
    assert count_after_second == 25
