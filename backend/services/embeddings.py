"""Embeddings service managing vector generation, input_type modes,
in-memory caching, and cosine similarity calculations.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from backend.core.config import settings
from backend.core.nvidia_client import nvidia_client

# In-memory query cache to reduce latency on repeated queries
_EMBED_CACHE: Dict[str, List[float]] = {}


async def embed_passage(text: str) -> Tuple[List[float], bool]:
    """Embed document passage / abstract using NVIDIA NIM passage mode."""
    return await nvidia_client.get_embedding(text=text, input_type="passage")


async def embed_query(text: str) -> Tuple[List[float], bool]:
    """Embed user search query using NVIDIA NIM query mode with caching."""
    cache_key = f"query:{text.strip()}"
    if cache_key in _EMBED_CACHE:
        return _EMBED_CACHE[cache_key], False

    vec, is_mock = await nvidia_client.get_embedding(text=text, input_type="query")
    _EMBED_CACHE[cache_key] = vec
    return vec, is_mock


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two numeric vectors [0.0, 1.0]."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    # Bound to [0.0, 1.0]
    return max(0.0, min(1.0, (similarity + 1.0) / 2.0 if similarity < 0 else similarity))
