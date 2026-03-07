import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/monitoring")

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if DATABASE_URL and "railway" in DATABASE_URL.lower() and "sslmode" not in DATABASE_URL:
            connect_args["sslmode"] = "require"
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # "company" or "person"
    created_at = Column(DateTime, default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="running")  # running, completed, failed


class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    entity_name = Column(String(255), nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(Text, nullable=False)
    snippet = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)


def init_db():
    Base.metadata.create_all(bind=get_engine())


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()
