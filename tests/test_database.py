"""Tests for SQLAlchemy database models and persistence operations.
"""

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, ProjectModel, PaperModel, ImportAuditModel, RunEventModel


@pytest.fixture
def test_db():
    """In-memory SQLite database session for unit testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_project_persistence(test_db):
    """Test project persistence and query."""
    p = ProjectModel(
        id="proj-test-1",
        name="Phishing ML Robustness",
        topic="Cross-dataset robustness of ML for phishing detection",
        year_range="2018-2024",
        status="active"
    )
    test_db.add(p)
    test_db.commit()

    retrieved = test_db.query(ProjectModel).filter(ProjectModel.id == "proj-test-1").first()
    assert retrieved is not None
    assert retrieved.name == "Phishing ML Robustness"
    assert retrieved.status == "active"


def test_paper_persistence_with_vectors(test_db):
    """Test paper record persistence with JSON-encoded vector embedding."""
    dummy_vec = [0.123] * 2048
    paper = PaperModel(
        paper_id="phish-01",
        title="Test Phishing Paper",
        authors_json=json.dumps(["Author One", "Author Two"]),
        year=2021,
        doi="10.1109/TEST.2021.001",
        source="IEEE Access",
        abstract="Comprehensive evaluation across benchmark datasets.",
        embedding_json=json.dumps(dummy_vec),
        embedding_model="nvidia/nemotron-3.5-embed-1b"
    )
    test_db.add(paper)
    test_db.commit()

    retrieved = test_db.query(PaperModel).filter(PaperModel.paper_id == "phish-01").first()
    assert retrieved is not None
    assert retrieved.title == "Test Phishing Paper"
    authors = json.loads(retrieved.authors_json)
    assert len(authors) == 2
    vec = json.loads(retrieved.embedding_json)
    assert len(vec) == 2048


def test_import_audit_persistence(test_db):
    """Test import audit logging."""
    audit = ImportAuditModel(
        source_type="bibtex",
        total_processed=5,
        imported_count=3,
        duplicate_count=2,
        rejected_count=0,
        details_json=json.dumps({"info": "test audit"})
    )
    test_db.add(audit)
    test_db.commit()

    res = test_db.query(ImportAuditModel).first()
    assert res.total_processed == 5
    assert res.imported_count == 3
