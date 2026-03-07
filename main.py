import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import init_db, get_db, SessionLocal, Entity, Run, Result

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Network Monitor", lifespan=lifespan)


# --- API ---

class EntityCreate(BaseModel):
    name: str
    type: str  # "company" or "person"


class EntityItem(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


@app.get("/api/entities", response_model=list[EntityItem])
def list_entities(db: Session = Depends(get_db)):
    return db.query(Entity).order_by(Entity.name).all()


@app.post("/api/entities", response_model=EntityItem)
def add_entity(body: EntityCreate, db: Session = Depends(get_db)):
    e = Entity(name=body.name.strip(), type=body.type)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@app.delete("/api/entities/{entity_id}", status_code=204)
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    e = db.query(Entity).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(e)
    db.commit()
    return None


def do_run(db: Session) -> list[dict]:
    """Run search for all entities. Returns list of results (mock for now)."""
    entities = db.query(Entity).all()
    run = Run(status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    results = []
    try:
        for e in entities:
            # Mock: one placeholder result per entity. Replace with real search later.
            hits = [
                {
                    "title": f"News about {e.name}",
                    "url": f"https://example.com/{e.name.replace(' ', '-')}",
                    "snippet": f"Recent content related to {e.name}.",
                    "source": "example.com",
                }
            ]
            for h in hits:
                r = Result(run_id=run.id, entity_name=e.name, title=h["title"], url=h["url"], snippet=h.get("snippet"), source=h.get("source"))
                db.add(r)
                results.append({"entity_name": e.name, "title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source})
        run.status = "completed"
    except Exception as ex:
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
            {"entity_name": r.entity_name, "title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source}
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
