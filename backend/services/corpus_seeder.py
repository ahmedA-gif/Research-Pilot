"""Corpus Seeder Service for loading and indexing the 25-paper benchmark corpus.
Ensures idempotent operations, generating 2048-dim passage embeddings.
"""

import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.db.models import PaperModel
from backend.schemas.contracts import PaperRecord, CorpusSeedResponse
from backend.services.embeddings import embed_passage

logger = logging.getLogger(__name__)


def load_seed_papers_file() -> List[dict]:
    """Load the 25 curated paper definitions from disk."""
    path = settings.SEED_PAPERS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Seed corpus file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_benchmark_corpus(db: Session, project_id: Optional[str] = None) -> CorpusSeedResponse:
    """Idempotently seed the 25 curated open-access papers into the database.
    Embeds each paper abstract using NVIDIA NIM passage mode.
    """
    raw_papers = load_seed_papers_file()

    seeded_count = 0
    skipped_count = 0
    resulting_records: List[PaperRecord] = []

    for item in raw_papers:
        p_id = item["paper_id"]
        p_doi = item.get("doi")
        p_title = item["title"]

        # Duplicate check: by paper_id or doi
        query = db.query(PaperModel).filter(
            (PaperModel.paper_id == p_id) |
            (PaperModel.doi == p_doi if p_doi else False)
        )
        existing = query.first()

        if existing:
            skipped_count += 1
            resulting_records.append(
                PaperRecord(
                    paper_id=existing.paper_id,
                    title=existing.title,
                    authors=json.loads(existing.authors_json),
                    year=existing.year,
                    doi=existing.doi,
                    source=existing.source,
                    abstract=existing.abstract,
                    open_access_url=existing.open_access_url,
                    embedding_model=existing.embedding_model,
                    embedding_version=existing.embedding_version
                )
            )
            continue

        # Generate passage embedding for abstract + title context
        embed_text = f"Title: {p_title}\nAbstract: {item['abstract']}"
        embedding_vec, _ = await embed_passage(embed_text)

        new_paper = PaperModel(
            paper_id=p_id,
            project_id=project_id,
            title=p_title,
            authors_json=json.dumps(item.get("authors", [])),
            year=item.get("year", 2022),
            doi=p_doi,
            source=item.get("source"),
            abstract=item.get("abstract", ""),
            open_access_url=item.get("open_access_url"),
            embedding_json=json.dumps(embedding_vec),
            embedding_model=settings.NVIDIA_EMBED_MODEL,
            embedding_version="1.0"
        )
        db.add(new_paper)
        seeded_count += 1
        resulting_records.append(
            PaperRecord(
                paper_id=p_id,
                title=p_title,
                authors=item.get("authors", []),
                year=item.get("year", 2022),
                doi=p_doi,
                source=item.get("source"),
                abstract=item.get("abstract", ""),
                open_access_url=item.get("open_access_url"),
                embedding_model=settings.NVIDIA_EMBED_MODEL,
                embedding_version="1.0"
            )
        )

    db.commit()
    total_count = db.query(PaperModel).count()

    return CorpusSeedResponse(
        status="success",
        seeded_count=seeded_count,
        skipped_count=skipped_count,
        total_corpus_count=total_count,
        papers=resulting_records
    )
