"""
Generate search queries per entity and call search provider. Returns list of raw hits.
MVP: mock search provider; replace with SerpAPI/Bing/News API later.
"""
import os
import sys
from typing import List, Dict, Any
import httpx

# Ensure shared and packages are on path when worker runs
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Optional: use env to point to a real search API
SEARCH_API_URL = os.environ.get("SEARCH_API_URL", "")
SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY", "")


def build_queries_for_entity(name: str, aliases: List[str]) -> List[str]:
    """Build search query strings for an entity (name + aliases)."""
    queries = [name]
    for a in (aliases or []):
        if a and a.strip() and a.strip() != name:
            queries.append(a.strip())
    return queries[:5]


def search_web(query: str, num: int = 10) -> List[Dict[str, Any]]:
    """
    Run web/news search for one query. MVP: mock results. Replace with real API call.
    """
    if SEARCH_API_URL and SEARCH_API_KEY:
        try:
            r = httpx.get(
                SEARCH_API_URL,
                params={"q": query, "num": num},
                headers={"Authorization": f"Bearer {SEARCH_API_KEY}"},
                timeout=15.0,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("results", data.get("items", []))
        except Exception:
            pass
    # Mock results for MVP
    return [
        {
            "title": f"News about {query}",
            "url": f"https://example.com/{query.replace(' ', '-')}-{i}",
            "snippet": f"Recent development related to {query}.",
            "source": "example.com",
        }
        for i in range(min(3, num))
    ]


def run_search_for_entities(entities_with_aliases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    entities_with_aliases: list of {entity_id, name, aliases: [str]}
    Returns flat list of hits with entity_id and query attached.
    """
    hits = []
    seen_urls = set()
    for ent in entities_with_aliases:
        name = ent.get("name", "")
        aliases = ent.get("aliases", [])
        entity_id = ent.get("entity_id")
        for q in build_queries_for_entity(name, aliases):
            results = search_web(q, num=10)
            for r in results:
                url = (r.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                hits.append({
                    "entity_id": entity_id,
                    "query": q,
                    "title": r.get("title", ""),
                    "url": url,
                    "snippet": r.get("snippet", ""),
                    "source": r.get("source"),
                })
    return hits
