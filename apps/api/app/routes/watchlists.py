from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.models import Watchlist, WatchlistEntity, Entity

from app.database import get_db
from app.schemas import WatchlistCreate, WatchlistUpdate, WatchlistResponse, EntityResponse

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=List[WatchlistResponse])
def list_watchlists(db: Session = Depends(get_db)):
    watchlists = db.query(Watchlist).order_by(Watchlist.updated_at.desc()).all()
    return [
        WatchlistResponse(
            id=w.id,
            name=w.name,
            entity_ids=[we.entity_id for we in w.entities],
            created_at=w.created_at,
            updated_at=w.updated_at,
        )
        for w in watchlists
    ]


@router.post("", response_model=WatchlistResponse)
def create_watchlist(body: WatchlistCreate, db: Session = Depends(get_db)):
    watchlist = Watchlist(name=body.name)
    db.add(watchlist)
    db.flush()
    for eid in body.entity_ids:
        db.add(WatchlistEntity(watchlist_id=watchlist.id, entity_id=eid))
    db.commit()
    db.refresh(watchlist)
    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        entity_ids=body.entity_ids,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return WatchlistResponse(
        id=w.id,
        name=w.name,
        entity_ids=[we.entity_id for we in w.entities],
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(watchlist_id: int, body: WatchlistUpdate, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if body.name is not None:
        w.name = body.name
    if body.entity_ids is not None:
        db.query(WatchlistEntity).filter(WatchlistEntity.watchlist_id == watchlist_id).delete()
        for eid in body.entity_ids:
            db.add(WatchlistEntity(watchlist_id=watchlist_id, entity_id=eid))
    db.commit()
    db.refresh(w)
    return WatchlistResponse(
        id=w.id,
        name=w.name,
        entity_ids=[we.entity_id for we in w.entities],
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    db.delete(w)
    db.commit()
    return None
