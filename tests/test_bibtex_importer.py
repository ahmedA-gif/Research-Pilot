"""Tests for DOI and BibTeX importer, normalization, and duplicate detection.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base
from backend.services.bibtex_importer import normalize_doi, import_bibtex_or_doi


@pytest.fixture
def import_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_normalize_doi():
    """Verify DOI normalization handles prefixes and case properly."""
    assert normalize_doi("10.1145/3374218.3374235") == "10.1145/3374218.3374235"
    assert normalize_doi("https://doi.org/10.1145/3374218.3374235") == "10.1145/3374218.3374235"
    assert normalize_doi("http://dx.doi.org/10.1109/ACCESS.2021.3060123") == "10.1109/access.2021.3060123"
    assert normalize_doi("not-a-doi") is None


@pytest.mark.asyncio
async def test_import_single_doi(import_db):
    """Test importing a single DOI string."""
    raw_doi = "https://doi.org/10.1145/3374218.3374235"
    res = await import_bibtex_or_doi(db=import_db, raw_content=raw_doi, project_id="proj-1")

    assert res.total_processed == 1
    assert res.imported_count == 1
    assert res.duplicate_count == 0
    assert res.records[0].status == "imported"
    assert res.records[0].doi == "10.1145/3374218.3374235"


@pytest.mark.asyncio
async def test_import_bibtex_entry_and_duplicate_detection(import_db):
    """Test importing a BibTeX entry and subsequently detecting it as duplicate."""
    bibtex_entry = """
    @article{smith2023robustness,
      title = {Robustness of Neural Phishing Classifiers},
      author = {Smith, John and Doe, Jane},
      year = {2023},
      doi = {10.1016/j.cose.2023.99999},
      journal = {Computers & Security},
      abstract = {An empirical investigation into temporal decay.}
    }
    """

    # 1. First import: should succeed
    res1 = await import_bibtex_or_doi(db=import_db, raw_content=bibtex_entry, project_id="proj-1")
    assert res1.imported_count == 1
    assert res1.duplicate_count == 0

    # 2. Second import: should be marked as duplicate
    res2 = await import_bibtex_or_doi(db=import_db, raw_content=bibtex_entry, project_id="proj-1")
    assert res2.imported_count == 0
    assert res2.duplicate_count == 1
    assert res2.records[0].status == "duplicate"
    assert "matches on DOI" in res2.records[0].merge_reason


@pytest.mark.asyncio
async def test_import_malformed_input(import_db):
    """Test importing completely malformed content."""
    res = await import_bibtex_or_doi(db=import_db, raw_content="Just some random unstructured text", project_id="proj-1")
    assert res.rejected_count == 1
    assert res.imported_count == 0
    assert res.records[0].status == "rejected"
