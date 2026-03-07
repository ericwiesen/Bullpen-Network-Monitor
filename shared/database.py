import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models import Base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/monitoring",
)


def get_engine():
    connect_args = {}
    if "railway" in DATABASE_URL.lower() and "sslmode" not in DATABASE_URL:
        connect_args["sslmode"] = "require"
    return create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)


def get_session_factory(engine=None):
    engine = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine=None):
    engine = engine or get_engine()
    Base.metadata.create_all(bind=engine)


def get_db(engine=None):
    factory = get_session_factory(engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()
