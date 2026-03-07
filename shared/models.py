from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class EntityType(str, enum.Enum):
    company = "company"
    person = "person"


class RunTrigger(str, enum.Enum):
    manual = "manual"
    scheduled = "scheduled"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ContentType(str, enum.Enum):
    news = "news"
    press_release = "press_release"
    blog = "blog"
    other = "other"


class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(EntityType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    aliases = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    watchlist_links = relationship("WatchlistEntity", back_populates="entity", cascade="all, delete-orphan")


class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    entity = relationship("Entity", back_populates="aliases")


class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entities = relationship("WatchlistEntity", back_populates="watchlist", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistEntity(Base):
    __tablename__ = "watchlist_entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    watchlist = relationship("Watchlist", back_populates="entities")
    entity = relationship("Entity", back_populates="watchlist_links")


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    trigger = Column(SQLEnum(RunTrigger), nullable=False)
    status = Column(SQLEnum(RunStatus), default=RunStatus.pending, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    watchlist = relationship("Watchlist", back_populates="runs")
    search_queries = relationship("SearchQuery", back_populates="run", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="run", cascade="all, delete-orphan")


class SearchQuery(Base):
    __tablename__ = "search_queries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    run = relationship("Run", back_populates="search_queries")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    source = Column(String(255), nullable=True)
    url = Column(Text, nullable=False, unique=False)
    published_at = Column(DateTime, nullable=True)
    snippet = Column(Text, nullable=True)
    content_type = Column(SQLEnum(ContentType), default=ContentType.other, nullable=False)
    relevance_score = Column(Float, nullable=True)
    canonical_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    run = relationship("Run", back_populates="documents")
    matches = relationship("DocumentMatch", back_populates="document", cascade="all, delete-orphan")
    summary_rel = relationship("Summary", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentMatch(Base):
    __tablename__ = "document_matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="matches")
    entity = relationship("Entity", backref="document_matches")


class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=True)
    relevance_label = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="summary_rel")
