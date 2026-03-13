from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from duckduckgo_search import DDGS
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database import init_db, get_db, Entity, Run, Result


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as e:
        print("Database init failed (set DATABASE_URL and retry):", e)
    yield


app = FastAPI(title="Network Monitor", lifespan=lifespan)


@app.exception_handler(OperationalError)
def db_error_handler(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database not connected. In Railway, add a Postgres plugin and link DATABASE_URL to this service."},
    )


@app.get("/api/health")
def health():
    """Railway can hit this to check the app is up. Does not touch the database."""
    return {"status": "ok"}


# --- API ---

class EntityCreate(BaseModel):
    name: str
    type: str  # "company" or "person"
    context: Optional[str] = None
    url: Optional[str] = None


class EntityItem(BaseModel):
    id: int
    name: str
    type: str
    context: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

    class Config:
        from_attributes = True


@app.get("/api/entities", response_model=list[EntityItem])
def list_entities(db: Session = Depends(get_db)):
    return db.query(Entity).order_by(Entity.name).all()


@app.post("/api/entities", response_model=EntityItem)
def add_entity(body: EntityCreate, db: Session = Depends(get_db)):
    name = body.name.strip()
    context = body.context.strip() if body.context else None
    provided_url = body.url.strip() if body.url else None
    e = Entity(name=name, type=body.type, context=context)
    db.add(e)
    db.commit()
    db.refresh(e)
    if body.type == "company" and provided_url:
        # Use the URL the user provided directly — no search needed
        e.url = provided_url
        db.commit()
        db.refresh(e)
    elif body.type == "person":
        info = lookup_entity(name, body.type, context)
        if info.get("description") or info.get("url"):
            e.description = info.get("description")
            e.url = info.get("url")
            db.commit()
            db.refresh(e)
    return e


def _looks_english(text: str) -> bool:
    """Returns False if more than 10% of characters are non-ASCII (likely foreign language)."""
    if not text:
        return True
    return sum(1 for c in text if ord(c) > 127) / len(text) < 0.10


def lookup_entity(name: str, entity_type: str, context: Optional[str] = None) -> dict:
    """Find a description and URL for the entity via DuckDuckGo web search."""
    query = " ".join(filter(None, [f'"{name}"', context, entity_type]))
    # Slugified name for domain matching (e.g. "AvantStay" → "avantstay")
    name_slug = name.lower().replace(" ", "").replace("-", "")
    first_word = name.lower().split()[0]
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="us-en", max_results=10))
        if not results:
            return {"description": None, "url": None}
        # Prefer English results
        english = [r for r in results if _looks_english(r.get("title", "") + r.get("body", ""))]
        candidates = english if english else results
        # 1st priority: domain contains the entity name slug (e.g. avantstay.com)
        for r in candidates:
            if name_slug in r.get("href", "").lower():
                return {"description": r.get("body"), "url": r.get("href")}
        # 2nd priority: title contains the first word of the name
        for r in candidates:
            if first_word in r.get("title", "").lower():
                return {"description": r.get("body"), "url": r.get("href")}
        # Fallback: first English result
        return {"description": candidates[0].get("body"), "url": candidates[0].get("href")}
    except Exception:
        pass
    return {"description": None, "url": None}


@app.delete("/api/entities/{entity_id}", status_code=204)
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    e = db.query(Entity).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(e)
    db.commit()
    return None


def do_run(db: Session) -> list[dict]:
    """Run DuckDuckGo news search for all entities, sort by recency, and store results."""
    entities = db.query(Entity).all()
    run = Run(status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        # Collect all hits across all entities
        all_hits = []
        for e in entities:
            query = f'"{e.name}" {e.context}' if e.context else f'"{e.name}"'
            try:
                with DDGS() as ddgs:
                    hits = list(ddgs.news(query, max_results=10, timelimit="m"))
            except Exception:
                hits = []
            for h in hits:
                all_hits.append((e.name, h))

        # Sort all hits by date descending (ISO strings sort correctly)
        all_hits.sort(key=lambda x: x[1].get("date", ""), reverse=True)

        # Store and build response in sorted order
        results = []
        for entity_name, h in all_hits:
            r = Result(
                run_id=run.id,
                entity_name=entity_name,
                title=h.get("title", ""),
                url=h.get("url", ""),
                snippet=h.get("body"),
                source=h.get("source"),
            )
            db.add(r)
            results.append({
                "entity_name": entity_name,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source,
                "date": h.get("date", ""),
            })
        run.status = "completed"
    except Exception:
        run.status = "failed"
        raise
    finally:
        db.commit()
    return results


@app.post("/api/run")
def run_search(db: Session = Depends(get_db)):
    """Run the monitor for all entities. Synchronous – may take a few seconds."""
    return do_run(db)


@app.get("/api/last-run")
def last_run_results(db: Session = Depends(get_db)):
    """Get results from the most recent run."""
    run = db.query(Run).order_by(Run.id.desc()).first()
    if not run:
        return {"run_id": None, "results": []}
    rows = db.query(Result).filter(Result.run_id == run.id).order_by(Result.id).all()
    return {
        "run_id": run.id,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "results": [
            {"entity_name": r.entity_name, "title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source, "date": ""}
            for r in rows
        ],
    }


# --- Serve UI ---

static_dir = Path(__file__).parent / "static"

@app.get("/")
def index():
    if static_dir.is_dir():
        return FileResponse(static_dir / "index.html")
    return {"message": "Network Monitor API. Add static/index.html for UI."}

if static_dir.is_dir():
    assets = static_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{rest:path}")
    def serve_spa(rest: str):
        return FileResponse(static_dir / "index.html")
