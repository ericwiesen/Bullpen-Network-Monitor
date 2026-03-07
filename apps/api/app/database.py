import os
from sqlalchemy.orm import Session
from app.config import settings
from shared.database import get_engine as _get_engine, get_session_factory, init_db as _init_db

os.environ.setdefault("DATABASE_URL", settings.database_url)
engine = _get_engine()
SessionLocal = get_session_factory(engine)


def init_db():
    _init_db(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
