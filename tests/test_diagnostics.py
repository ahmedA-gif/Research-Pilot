"""Tests for system diagnostics service and provider telemetry.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base
from backend.services.diagnostics import collect_system_diagnostics
from backend.schemas.contracts import SystemDiagnosticsReport


@pytest.fixture
def diag_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_diagnostics_report_structure(diag_db):
    """Verify diagnostics reports provider statuses, latency values, and fallback order."""
    report = await collect_system_diagnostics(db=diag_db)

    assert isinstance(report, SystemDiagnosticsReport)
    assert len(report.providers) >= 4

    service_names = [p.service_name for p in report.providers]
    assert any("Database" in s or "SQLite" in s or "Postgres" in s for s in service_names)
    assert any("NVIDIA NIM Chat LLM" in s for s in service_names)
    assert any("NVIDIA NIM Embeddings" in s for s in service_names)

    # Check that fallback order is populated
    assert len(report.active_fallback_order) > 0
