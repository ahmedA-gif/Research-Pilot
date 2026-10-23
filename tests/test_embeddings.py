"""Tests for embeddings service, vector properties, and cosine similarity.
"""

import pytest
from backend.services.embeddings import embed_passage, embed_query, compute_cosine_similarity
from backend.core.config import settings


@pytest.mark.asyncio
async def test_embed_passage_properties():
    """Verify that embed_passage returns a 2048-dim normalized vector."""
    text = "Machine learning classifiers suffer degradation across disparate phishing datasets."
    vec, is_mock = await embed_passage(text)

    assert isinstance(vec, list)
    assert len(vec) == settings.EMBEDDING_DIMENSION  # 2048
    assert all(isinstance(x, (float, int)) for x in vec)


@pytest.mark.asyncio
async def test_embed_query_properties():
    """Verify that embed_query returns a 2048-dim vector."""
    query = "concept drift in phishing URL classification"
    vec, is_mock = await embed_query(query)

    assert isinstance(vec, list)
    assert len(vec) == settings.EMBEDDING_DIMENSION  # 2048


@pytest.mark.asyncio
async def test_embed_empty_text_error():
    """Verify that embedding empty text raises ValueError."""
    with pytest.raises(ValueError):
        await embed_passage("")


def test_cosine_similarity_bounds_and_symmetry():
    """Verify cosine similarity calculation properties."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    # Identical vectors -> similarity 1.0
    assert pytest.approx(compute_cosine_similarity(v1, v2), 0.001) == 1.0

    # Orthogonal vectors -> bounded in [0.0, 1.0]
    score_ortho = compute_cosine_similarity(v1, v3)
    assert 0.0 <= score_ortho <= 1.0

    # Symmetry
    assert compute_cosine_similarity(v1, v3) == compute_cosine_similarity(v3, v1)
