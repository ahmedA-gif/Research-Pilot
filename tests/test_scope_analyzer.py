"""Tests for topic scope analyzer service and PICO-CS validation.
"""

import pytest
from backend.schemas.contracts import ScopeAnalysisRequest, ScopeAnalysisResult
from backend.services.scope_analyzer import analyze_topic_scope


@pytest.mark.asyncio
async def test_scope_analysis_returns_valid_structure():
    """Verify that scope analysis produces a fully valid ScopeAnalysisResult with 3 RQs."""
    req = ScopeAnalysisRequest(
        topic="Cross-dataset robustness of machine learning methods for phishing detection",
        constraints="Focus on lexical and DOM structural feature decay"
    )
    result = await analyze_topic_scope(req)

    assert isinstance(result, ScopeAnalysisResult)
    assert result.original_topic == req.topic
    assert len(result.research_questions) == 3
    assert 0 <= result.feasibility_score <= 100
    assert result.boolean_queries.openalex
    assert result.boolean_queries.arxiv
    assert result.boolean_queries.github
    assert len(result.problem) > 10
    assert len(result.method) > 10
    assert len(result.comparison) > 10
    assert len(result.outcomes) > 10
