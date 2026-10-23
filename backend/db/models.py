"""SQLAlchemy 2.0 ORM models for ResearchPilot.
Stores projects, papers, embeddings, import audits, and pipeline run events.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    topic = Column(Text, nullable=False)
    constraints = Column(Text, nullable=True)
    year_range = Column(String(64), default="2018-2024")
    status = Column(String(64), default="active")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    papers = relationship("PaperModel", back_populates="project", cascade="all, delete-orphan")


class PaperModel(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(64), unique=True, index=True, nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    authors_json = Column(Text, nullable=False)  # JSON-serialized list of author names
    year = Column(Integer, nullable=False, index=True)
    doi = Column(String(255), unique=True, index=True, nullable=True)
    source = Column(String(255), nullable=True)
    abstract = Column(Text, nullable=False)
    open_access_url = Column(String(1024), nullable=True)
    
    # Vector Embedding (JSON string of 2048 float values, compatible with SQLite and pgvector)
    embedding_json = Column(Text, nullable=True)
    embedding_model = Column(String(128), default="nvidia/nemotron-3.5-embed-1b")
    embedding_version = Column(String(64), default="1.0")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("ProjectModel", back_populates="papers")


class ImportAuditModel(Base):
    __tablename__ = "import_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), nullable=True, index=True)
    source_type = Column(String(64), nullable=False)  # bibtex, doi, seed
    total_processed = Column(Integer, default=0)
    imported_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class RunEventModel(Base):
    __tablename__ = "run_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), index=True, nullable=False)
    correlation_id = Column(String(64), index=True, nullable=False)
    task_id = Column(String(64), nullable=False)
    stage = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    error_json = Column(Text, nullable=True)
    simulation_mode = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
