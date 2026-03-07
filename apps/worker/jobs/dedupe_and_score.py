"""
Deduplicate by canonical URL and title similarity; assign relevance score; persist documents and matches.
"""
import os
import sys
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.models import Document, DocumentMatch, ContentType, RunStatus
from sqlalchemy.orm import Session


def canonical_url(url: str) -> str:
    """Normalize URL for deduplication (scheme + netloc + path, lowercased)."""
    try:
        p = urlparse(url)
        path = (p.path or "/").rstrip("/") or "/"
        return urlunparse((p.scheme or "https", (p.netloc or "").lower(), path, "", "", "")).lower()
    except Exception:
        return url.lower()


def title_similarity(a: str, b: str) -> float:
    """Simple Jaccard-like similarity on words. Returns 0..1."""
    if not a or not b:
        return 0.0
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def relevance_score(doc: Dict[str, Any], entity_name: str) -> float:
    """Score 0..1 based on snippet/title containing entity name and content type."""
    score = 0.5
    title = (doc.get("title") or "").lower()
    snippet = (doc.get("snippet") or "").lower()
    name = entity_name.lower()
    if name in title:
        score += 0.25
    if name in snippet:
        score += 0.15
    ct = doc.get("content_type", "other")
    if ct == "press_release":
        score += 0.05
    if ct == "news":
        score += 0.03
    return min(1.0, score)


def dedupe_and_persist(
    session: Session,
    run_id: int,
    normalized_docs: List[Dict[str, Any]],
    entity_names_by_id: Dict[int, str],
) -> None:
    """
    Dedupe by canonical URL (and optionally title), score, then insert Document and DocumentMatch.
    normalized_docs: list of dicts with run_id, title, source, url, published_at, snippet, content_type, entity_id.
    """
    seen_canonical = {}
    for d in normalized_docs:
        url = d.get("url", "")
        can = canonical_url(url)
        if can in seen_canonical:
            existing = seen_canonical[can]
            existing_entity_ids = {m["entity_id"] for m in existing.get("matches", [])}
            if d.get("entity_id") not in existing_entity_ids:
                existing.setdefault("matches", []).append({"entity_id": d["entity_id"]})
            continue
        doc_copy = {k: v for k, v in d.items() if k != "entity_id"}
        doc_copy["canonical_url"] = can
        doc_copy["matches"] = [{"entity_id": d["entity_id"]}]
        seen_canonical[can] = doc_copy

    for doc_dict in seen_canonical.values():
        matches = doc_dict.pop("matches", [])
        entity_ids = [m["entity_id"] for m in matches]
        name = entity_names_by_id.get(entity_ids[0], "") if entity_ids else ""
        doc_dict["relevance_score"] = relevance_score(doc_dict, name)
        ct = doc_dict.get("content_type", "other")
        doc_dict["content_type"] = ContentType.news if ct == "news" else (
            ContentType.press_release if ct == "press_release" else (
                ContentType.blog if ct == "blog" else ContentType.other
            )
        )
        doc = Document(**{k: v for k, v in doc_dict.items() if k in (
            "run_id", "title", "source", "url", "published_at", "snippet", "content_type",
            "relevance_score", "canonical_url"
        )})
        session.add(doc)
        session.flush()
        for eid in entity_ids:
            session.add(DocumentMatch(document_id=doc.id, entity_id=eid))
    session.commit()
