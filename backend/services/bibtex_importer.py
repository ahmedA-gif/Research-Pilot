"""DOI and BibTeX Importer Service.
Parses, validates, normalizes DOIs, handles duplicate detection with audit trails.
"""

import json
import re
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.db.models import PaperModel, ImportAuditModel
from backend.schemas.contracts import ImportedRecord, BibTeXImportResponse
from backend.services.embeddings import embed_passage


def normalize_doi(raw_doi: Optional[str]) -> Optional[str]:
    """Normalize DOI to standard lowercase prefix '10.xxxx/yyyy'."""
    if not raw_doi:
        return None
    cleaned = raw_doi.strip()
    # Strip URL prefixes
    cleaned = re.sub(r"^https?://(dx\.)?doi\.org/", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^doi:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip().lower()
    if re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", cleaned):
        return cleaned
    return None


def parse_bibtex_entries(raw_text: str) -> List[dict]:
    """Basic regex-based BibTeX parser for title, author, year, doi, abstract, journal."""
    entries = []
    # Match @type{key, ...}
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),([^@]*)\}", re.DOTALL)
    for match in pattern.finditer(raw_text):
        entry_type = match.group(1).lower()
        cite_key = match.group(2).strip()
        body = match.group(3)

        fields = {}
        # Match field = {value} or field = "value" or field = number
        field_matches = re.finditer(
            r'(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|(\d+))',
            body,
            re.DOTALL
        )
        for fm in field_matches:
            k = fm.group(1).lower()
            val = fm.group(2) or fm.group(3) or fm.group(4) or ""
            fields[k] = " ".join(val.replace("\n", " ").split())

        title = fields.get("title", "")
        author_raw = fields.get("author", fields.get("authors", ""))
        authors = [a.strip() for a in author_raw.split(" and ")] if author_raw else ["Unknown Author"]
        year_str = fields.get("year", "2023")
        try:
            year = int(re.search(r"\d{4}", year_str).group(0))
        except Exception:
            year = 2023

        doi = normalize_doi(fields.get("doi"))
        source = fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or entry_type.capitalize()
        abstract = fields.get("abstract", f"Scientific paper regarding {title}")

        entries.append({
            "key": cite_key,
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "source": source,
            "abstract": abstract
        })
    return entries


async def import_bibtex_or_doi(
    db: Session,
    raw_content: str,
    project_id: Optional[str] = None,
    default_source: str = "Manual Import"
) -> BibTeXImportResponse:
    """Parse, validate, and persist BibTeX or raw DOI records."""
    imported_records: List[ImportedRecord] = []
    entries_to_process = []

    content_clean = raw_content.strip()

    # Check if raw_content is a single or list of DOIs
    doi_candidate = normalize_doi(content_clean)
    if doi_candidate:
        entries_to_process.append({
            "key": f"doi-{uuid.uuid4().hex[:6]}",
            "title": f"Paper Indexed via DOI: {doi_candidate}",
            "authors": ["External Author"],
            "year": 2023,
            "doi": doi_candidate,
            "source": default_source,
            "abstract": f"Directly imported research publication registered under DOI {doi_candidate}."
        })
    else:
        # Parse as BibTeX
        bib_entries = parse_bibtex_entries(content_clean)
        if bib_entries:
            entries_to_process.extend(bib_entries)
        else:
            # Fallback: check if lines contain DOIs
            lines = [line.strip() for line in content_clean.splitlines() if line.strip()]
            for line in lines:
                nd = normalize_doi(line)
                if nd:
                    entries_to_process.append({
                        "key": f"doi-{uuid.uuid4().hex[:6]}",
                        "title": f"Paper Indexed via DOI: {nd}",
                        "authors": ["External Author"],
                        "year": 2023,
                        "doi": nd,
                        "source": default_source,
                        "abstract": f"Directly imported research publication registered under DOI {nd}."
                    })

    if not entries_to_process:
        # Rejected due to empty or unparseable format
        audit = ImportAuditModel(
            project_id=project_id,
            source_type="bibtex_or_doi",
            total_processed=1,
            imported_count=0,
            duplicate_count=0,
            rejected_count=1,
            details_json=json.dumps({"error": "No valid BibTeX blocks or DOIs could be parsed."})
        )
        db.add(audit)
        db.commit()
        return BibTeXImportResponse(
            total_processed=1,
            imported_count=0,
            duplicate_count=0,
            rejected_count=1,
            records=[
                ImportedRecord(
                    paper_id="invalid",
                    title="Malformed Payload",
                    authors=[],
                    year=0,
                    status="rejected",
                    abstract="",
                    merge_reason="Failed to parse valid BibTeX syntax or normalized DOI."
                )
            ]
        )

    imported_cnt = 0
    duplicate_cnt = 0
    rejected_cnt = 0

    for item in entries_to_process:
        title = item["title"]
        doi = item["doi"]

        if not title:
            rejected_cnt += 1
            imported_records.append(
                ImportedRecord(
                    paper_id=item["key"],
                    title="Missing Title",
                    authors=item["authors"],
                    year=item["year"],
                    doi=doi,
                    abstract="",
                    status="rejected",
                    merge_reason="Paper title is required."
                )
            )
            continue

        # Duplicate check: first by normalized DOI, then by title match
        existing_paper = None
        if doi:
            existing_paper = db.query(PaperModel).filter(PaperModel.doi == doi).first()
        if not existing_paper:
            existing_paper = db.query(PaperModel).filter(PaperModel.title.ilike(title.strip())).first()

        if existing_paper:
            duplicate_cnt += 1
            imported_records.append(
                ImportedRecord(
                    paper_id=existing_paper.paper_id,
                    title=existing_paper.title,
                    authors=json.loads(existing_paper.authors_json),
                    year=existing_paper.year,
                    doi=existing_paper.doi,
                    source=existing_paper.source,
                    abstract=existing_paper.abstract,
                    status="duplicate",
                    merge_reason=f"Existing record matches on {'DOI: ' + doi if doi else 'Title'}."
                )
            )
            continue

        # New record: generate passage embedding and persist
        p_id = f"import-{uuid.uuid4().hex[:8]}"
        embed_text = f"Title: {title}\nAbstract: {item['abstract']}"
        embedding_vec, _ = await embed_passage(embed_text)

        new_paper = PaperModel(
            paper_id=p_id,
            project_id=project_id,
            title=title,
            authors_json=json.dumps(item["authors"]),
            year=item["year"],
            doi=doi,
            source=item["source"],
            abstract=item["abstract"],
            open_access_url=f"https://doi.org/{doi}" if doi else None,
            embedding_json=json.dumps(embedding_vec),
            embedding_model=settings.NVIDIA_EMBED_MODEL,
            embedding_version="1.0"
        )
        db.add(new_paper)
        imported_cnt += 1

        imported_records.append(
            ImportedRecord(
                paper_id=p_id,
                title=title,
                authors=item["authors"],
                year=item["year"],
                doi=doi,
                source=item["source"],
                abstract=item["abstract"],
                status="imported",
                merge_reason="Successfully parsed, embedded, and indexed."
            )
        )

    db.commit()

    # Record audit log
    audit = ImportAuditModel(
        project_id=project_id,
        source_type="bibtex_or_doi",
        total_processed=len(entries_to_process),
        imported_count=imported_cnt,
        duplicate_count=duplicate_cnt,
        rejected_count=rejected_cnt,
        details_json=json.dumps([r.model_dump() for r in imported_records])
    )
    db.add(audit)
    db.commit()

    return BibTeXImportResponse(
        total_processed=len(entries_to_process),
        imported_count=imported_cnt,
        duplicate_count=duplicate_cnt,
        rejected_count=rejected_cnt,
        records=imported_records
    )
