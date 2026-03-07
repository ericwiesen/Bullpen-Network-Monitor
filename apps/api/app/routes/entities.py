from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.models import Entity, EntityAlias, EntityType

from app.database import get_db
from app.schemas import EntityCreate, EntityResponse

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=List[EntityResponse])
def list_entities(db: Session = Depends(get_db)):
    entities = db.query(Entity).order_by(Entity.name).all()
    return [
        EntityResponse(
            id=e.id,
            name=e.name,
            type=e.type,
            aliases=[a.alias for a in e.aliases],
            created_at=e.created_at,
        )
        for e in entities
    ]


@router.post("", response_model=EntityResponse)
def create_entity(body: EntityCreate, db: Session = Depends(get_db)):
    entity = Entity(name=body.name, type=body.type)
    db.add(entity)
    db.flush()
    for a in body.aliases or []:
        db.add(EntityAlias(entity_id=entity.id, alias=a.alias))
    db.commit()
    db.refresh(entity)
    return EntityResponse(
        id=entity.id,
        name=entity.name,
        type=entity.type,
        aliases=[a.alias for a in entity.aliases],
        created_at=entity.created_at,
    )


@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    e = db.query(Entity).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityResponse(
        id=e.id,
        name=e.name,
        type=e.type,
        aliases=[a.alias for a in e.aliases],
        created_at=e.created_at,
    )


@router.delete("/{entity_id}", status_code=204)
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    e = db.query(Entity).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(e)
    db.commit()
    return None
