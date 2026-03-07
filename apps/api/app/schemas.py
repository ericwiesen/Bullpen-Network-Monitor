from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from shared.models import EntityType, RunTrigger, RunStatus, ContentType


class EntityAliasCreate(BaseModel):
    alias: str


class EntityCreate(BaseModel):
    name: str
    type: EntityType
    aliases: Optional[List[EntityAliasCreate]] = []


class EntityResponse(BaseModel):
    id: int
    name: str
    type: EntityType
    aliases: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistEntityRef(BaseModel):
    entity_id: int


class WatchlistCreate(BaseModel):
    name: str
    entity_ids: List[int] = []


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    entity_ids: Optional[List[int]] = None


class WatchlistResponse(BaseModel):
    id: int
    name: str
    entity_ids: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunResponse(BaseModel):
    id: int
    watchlist_id: int
    trigger: RunTrigger
    status: RunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RunCreate(BaseModel):
    watchlist_id: int
    trigger: RunTrigger = RunTrigger.manual


class DocumentMatchResponse(BaseModel):
    entity_id: int
    entity_name: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    run_id: int
    title: str
    source: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    snippet: Optional[str] = None
    content_type: ContentType
    relevance_score: Optional[float] = None
    matched_entities: List[DocumentMatchResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    summary_text: Optional[str] = None
    relevance_label: Optional[str] = None
