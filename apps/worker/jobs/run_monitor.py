"""
Orchestrate one monitoring run: search -> fetch -> dedupe/score -> persist.
"""
import os
import sys
from datetime import datetime

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/monitoring"))

from sqlalchemy.orm import Session
from shared.database import get_engine, get_session_factory
from shared.models import Run, RunStatus, Watchlist, Entity, SearchQuery

from jobs.search_entities import run_search_for_entities
from jobs.fetch_content import fetch_and_extract, normalize_document
from jobs.dedupe_and_score import dedupe_and_persist


def run_watchlist(run_id: int) -> None:
    engine = get_engine()
    session_factory = get_session_factory(engine)
    db: Session = session_factory()

    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        db.close()
        return
    run.status = RunStatus.running
    db.commit()

    try:
        watchlist = db.query(Watchlist).filter(Watchlist.id == run.watchlist_id).first()
        if not watchlist:
            run.status = RunStatus.failed
            run.error_message = "Watchlist not found"
            run.completed_at = datetime.utcnow()
            db.commit()
            db.close()
            return

        entities_with_aliases = []
        entity_names_by_id = {}
        for we in watchlist.entities:
            e = db.query(Entity).filter(Entity.id == we.entity_id).first()
            if not e:
                continue
            entity_names_by_id[e.id] = e.name
            entities_with_aliases.append({
                "entity_id": e.id,
                "name": e.name,
                "aliases": [a.alias for a in e.aliases],
            })

        if not entities_with_aliases:
            run.status = RunStatus.completed
            run.completed_at = datetime.utcnow()
            db.commit()
            db.close()
            return

        hits = run_search_for_entities(entities_with_aliases)

        for h in hits:
            db.add(SearchQuery(run_id=run_id, entity_id=h["entity_id"], query_text=h.get("query", "")))
        db.commit()

        normalized_docs = []
        for hit in hits:
            fetched = fetch_and_extract(
                hit["url"],
                existing_title=hit.get("title", ""),
                existing_snippet=hit.get("snippet", ""),
            )
            norm = normalize_document(hit, fetched, run_id)
            normalized_docs.append(norm)

        dedupe_and_persist(db, run_id, normalized_docs, entity_names_by_id)

        run.status = RunStatus.completed
        run.completed_at = datetime.utcnow()
        run.error_message = None
        db.commit()
    except Exception as e:
        run.status = RunStatus.failed
        run.completed_at = datetime.utcnow()
        run.error_message = str(e)
        db.commit()
    finally:
        db.close()
