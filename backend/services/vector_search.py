"""Vector Search Service performing cosine similarity search over paper embeddings.
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.db.models import PaperModel
from backend.schemas.contracts import ScoredPaper, VectorSearchResponse
from backend.services.embeddings import embed_query, compute_cosine_similarity


async def search_corpus_by_vector(
    db: Session,
    query: str,
    project_id: Optional[str] = None,
    limit: int = 10
) -> VectorSearchResponse:
    """Embed the user query in query mode and rank stored paper vectors by cosine similarity."""
    if not query or not query.strip():
        return VectorSearchResponse(
            query=query,
            total_matches=0,
            papers=[],
            model_id=settings.NVIDIA_EMBED_MODEL,
            dimension=settings.EMBEDDING_DIMENSION
        )

    # 1. Generate query embedding
    query_vec, _ = await embed_query(query)

    # 2. Fetch all candidate papers from database
    q_filter = db.query(PaperModel)
    if project_id:
        q_filter = q_filter.filter(
            (PaperModel.project_id == project_id) |
            (PaperModel.project_id.is_(None)) |
            (PaperModel.paper_id.like("phish-%"))
        )
    papers = q_filter.all()

    # 3. Compute cosine similarity for each paper
    scored_results: List[ScoredPaper] = []
    for p in papers:
        if not p.embedding_json:
            continue
        try:
            p_vec = json.loads(p.embedding_json)
            score = compute_cosine_similarity(query_vec, p_vec)
            scored_results.append(
                ScoredPaper(
                    paper_id=p.paper_id,
                    title=p.title,
                    authors=json.loads(p.authors_json),
                    year=p.year,
                    doi=p.doi,
                    source=p.source,
                    abstract=p.abstract,
                    open_access_url=p.open_access_url,
                    similarity_score=round(score, 4)
                )
            )
        except Exception:
            continue

    # 4. Sort descending by similarity score
    scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
    top_k = scored_results[:limit]

    return VectorSearchResponse(
        query=query,
        total_matches=len(top_k),
        papers=top_k,
        model_id=settings.NVIDIA_EMBED_MODEL,
        dimension=settings.EMBEDDING_DIMENSION
    )
