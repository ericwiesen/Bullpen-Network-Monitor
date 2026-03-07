import os
import sys
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from shared.models import Run, Watchlist, Document, DocumentMatch, Entity, RunTrigger, RunStatus

from app.database import get_db
from app.schemas import RunResponse, RunCreate, DocumentResponse, DocumentMatchResponse
from app.config import settings

router = APIRouter(prefix="/runs", tags=["runs"])

# Enqueue run job (worker will pick up)
def enqueue_run(run_id: int):
    try:
        import redis
        from rq import Queue
        r = redis.from_url(settings.redis_url)
        q = Queue("default", connection=r)
        # Worker module path
        q.enqueue("jobs.run_monitor.run_watchlist", run_id, job_timeout="30m")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Queue unavailable: {e}")


@router.get("", response_model=List[RunResponse])
def list_runs(
    watchlist_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Run).order_by(Run.started_at.desc())
    if watchlist_id is not None:
        q = q.filter(Run.watchlist_id == watchlist_id)
    runs = q.limit(limit).all()
    return [RunResponse.model_validate(r) for r in runs]


@router.post("/schedule", response_model=List[RunResponse])
def schedule_all_watchlists(db: Session = Depends(get_db)):
    """Create and enqueue one scheduled run per watchlist. Call from cron for daily/hourly monitoring."""
    watchlists = db.query(Watchlist).all()
    created = []
    for w in watchlists:
        run = Run(watchlist_id=w.id, trigger=RunTrigger.scheduled, status=RunStatus.pending)
        db.add(run)
        db.flush()
        enqueue_run(run.id)
        created.append(run)
    db.commit()
    for r in created:
        db.refresh(r)
    return [RunResponse.model_validate(r) for r in created]


@router.post("", response_model=RunResponse)
def create_run(body: RunCreate, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.id == body.watchlist_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    run = Run(watchlist_id=body.watchlist_id, trigger=body.trigger, status=RunStatus.pending)
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue_run(run.id)
    return RunResponse.model_validate(run)


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    r = db.query(Run).filter(Run.id == run_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(r)


@router.get("/{run_id}/documents", response_model=List[DocumentResponse])
def list_run_documents(
    run_id: int,
    entity_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    r = db.query(Run).filter(Run.id == run_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    q = db.query(Document).filter(Document.run_id == run_id).order_by(Document.created_at.desc())
    if entity_id is not None:
        q = q.join(DocumentMatch).filter(DocumentMatch.entity_id == entity_id)
    docs = q.limit(limit).all()
    entity_ids = {e.id: e.name for e in db.query(Entity).all()}
    return [
        DocumentResponse(
            id=d.id,
            run_id=d.run_id,
            title=d.title,
            source=d.source,
            url=d.url,
            published_at=d.published_at,
            snippet=d.snippet,
            content_type=d.content_type,
            relevance_score=d.relevance_score,
            matched_entities=[
                DocumentMatchResponse(entity_id=m.entity_id, entity_name=entity_ids.get(m.entity_id))
                for m in d.matches
            ],
            created_at=d.created_at,
        )
        for d in docs
    ]
