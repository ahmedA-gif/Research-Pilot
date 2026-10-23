"""Tests for Pydantic v2 data contracts.
Verifies field requirements, validations, serialization, and edge cases.
"""

from datetime import datetime
import pytest
from pydantic import ValidationError
from backend.schemas.contracts import (
    Project,
    ProjectCreate,
    PaperRecord,
    ScopeAnalysisResult,
    BooleanQueries,
    TaskEnvelope,
    ProviderDiagnosticItem,
    SystemDiagnosticsReport,
    EvidenceSpan,
    PaperProfile,
    ResourceRecord,
    GraphNode,
    GraphEdge,
    CandidateGap,
    ExperimentPlan,
    VerificationAudit
)


def test_project_contract_validation():
    """Test valid and invalid Project and ProjectCreate payloads."""
    # Valid
    p = ProjectCreate(
        name="Phishing Robustness Study",
        topic="Cross-dataset robustness of ML for phishing detection",
        year_range="2018-2024"
    )
    assert p.name == "Phishing Robustness Study"

    # Too short topic
    with pytest.raises(ValidationError):
        ProjectCreate(name="Valid Name", topic="Short")


def test_scope_analysis_three_rqs_enforced():
    """Verify that ScopeAnalysisResult strictly requires exactly 3 research questions."""
    valid_payload = {
        "original_topic": "Phishing detection robustness",
        "problem": "Classifier accuracy collapse under domain shift",
        "method": "Multi-modal DOM and URL representation learning",
        "comparison": "Baseline Random Forest and character CNNs",
        "outcomes": "Cross-dataset transferability and low false positive rate",
        "research_questions": [
            "RQ1: How severe is accuracy decay across unaligned phishing datasets?",
            "RQ2: What invariant features maximize generalizability across time?",
            "RQ3: Can multi-modal graphs mitigate evasion bypasses?"
        ],
        "boolean_queries": {
            "openalex": "phishing AND machine learning",
            "arxiv": "phishing AND robustness",
            "github": "phishing-detection"
        },
        "feasibility_score": 85,
        "verdict": "Feasible and Well-Scoped",
        "warnings": ["Ensure longitudinal dataset splitting"]
    }

    # Should succeed with 3 RQs
    result = ScopeAnalysisResult.model_validate(valid_payload)
    assert len(result.research_questions) == 3
    assert result.feasibility_score == 85

    # Should fail with only 2 RQs
    invalid_2_rqs = dict(valid_payload)
    invalid_2_rqs["research_questions"] = [
        "RQ1: Only one question here?",
        "RQ2: And a second question here?"
    ]
    with pytest.raises(ValidationError) as exc:
        ScopeAnalysisResult.model_validate(invalid_2_rqs)
    assert "Expected exactly 3 research questions" in str(exc.value)

    # Should fail if feasibility score is outside [0, 100]
    invalid_score = dict(valid_payload)
    invalid_score["feasibility_score"] = 105
    with pytest.raises(ValidationError):
        ScopeAnalysisResult.model_validate(invalid_score)


def test_task_envelope_contract():
    """Verify TaskEnvelope schema, timestamps, and default simulation_mode."""
    envelope = TaskEnvelope(
        run_id="run-101",
        correlation_id="corr-555",
        task_id="task-01",
        stage="Topic Scope Analyzer",
        status="completed",
        payload={"feasibility": 90},
        simulation_mode=True
    )
    assert envelope.run_id == "run-101"
    assert envelope.simulation_mode is True
    assert isinstance(envelope.timestamp, datetime)
    dumped = envelope.model_dump()
    assert dumped["status"] == "completed"


def test_provider_diagnostics_contract():
    """Verify ProviderDiagnosticItem and SystemDiagnosticsReport schemas."""
    item = ProviderDiagnosticItem(
        service_name="NVIDIA NIM Chat LLM",
        configured=True,
        status="online",
        measured_latency_ms=145.2,
        fallback_tier="Tier 1",
        model_id="nvidia/nemotron-3-super-120b-a12b"
    )
    assert item.status == "online"
    assert item.measured_latency_ms == 145.2

    report = SystemDiagnosticsReport(
        providers=[item],
        active_fallback_order=["NVIDIA NIM", "Mock Fallback"],
        cache_hit_ratio=0.88
    )
    assert len(report.providers) == 1
    assert report.cache_hit_ratio == 0.88


def test_future_work_contracts_instantiation():
    """Verify future work contracts (EvidenceSpan, GraphNode, etc.) instantiate properly."""
    span = EvidenceSpan(
        span_id="span-1",
        paper_id="paper-01",
        quote="Accuracy dropped by 34% across datasets.",
        section="Results",
        page=4,
        confidence=0.98
    )
    assert span.confidence == 0.98

    profile = PaperProfile(
        paper_id="paper-01",
        primary_methods=["Random Forest", "SVM"],
        datasets_used=["PhishTank", "Alexa"],
        findings=["Severe distribution shift"],
        limitations=["Small sample size"]
    )
    assert "Random Forest" in profile.primary_methods

    node = GraphNode(id="n-1", label="PhishingClassifier", type="Model")
    edge = GraphEdge(source="n-1", target="n-2", relation="evaluated_on")
    assert edge.relation == "evaluated_on"

    gap = CandidateGap(
        id="gap-1",
        title="Temporal evaluation deficit",
        description="Few papers test on prospective longitudinal feeds",
        reason="Convenience of random k-fold splits",
        priority="high"
    )
    assert gap.priority == "high"

    plan = ExperimentPlan(
        id="exp-1",
        title="Cross-Domain Benchmark",
        hypothesis="DOM features reduce decay",
        methodology="Longitudinal crawl testing",
        evaluation_metrics=["AUC-ROC", "F1"]
    )
    assert len(plan.evaluation_metrics) == 2

    audit = VerificationAudit(
        audit_id="aud-1",
        status="passed",
        checks=[{"name": "Data Leakage Check", "passed": True}]
    )
    assert audit.status == "passed"
