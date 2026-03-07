"""
Fetch URL and extract title/snippet/date. Normalize to a common document shape.
"""
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import trafilatura
except ImportError:
    trafilatura = None


def fetch_and_extract(url: str, existing_title: str = "", existing_snippet: str = "") -> Dict[str, Any]:
    """
    Fetch URL and extract main content. Returns dict with title, snippet, published_at, content_type hint.
    """
    out = {
        "title": existing_title or url,
        "snippet": existing_snippet,
        "published_at": None,
        "content_type": "other",
    }
    try:
        r = httpx.get(url, follow_redirects=True, timeout=10.0)
        r.raise_for_status()
        html = r.text
        if trafilatura:
            doc = trafilatura.extract(html, include_comments=False, include_tables=False)
            if doc:
                out["snippet"] = (doc[:500] + "...") if len(doc) > 500 else doc
            parsed = trafilatura.extract_metadata(html)
            if parsed and parsed.date:
                try:
                    out["published_at"] = parsed.date
                except Exception:
                    pass
            if parsed and parsed.title:
                out["title"] = parsed.title
        else:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.string:
                out["title"] = soup.title.string.strip()
            for p in soup.find_all("p")[:3]:
                t = p.get_text(strip=True)
                if t and len(t) > 20:
                    out["snippet"] = (t[:500] + "...") if len(t) > 500 else t
                    break
    except Exception:
        pass
    return out


def normalize_document(
    hit: Dict[str, Any],
    fetched: Dict[str, Any],
    run_id: int,
) -> Dict[str, Any]:
    """Build normalized document dict for DB (title, source, url, published_at, snippet, content_type, run_id)."""
    return {
        "run_id": run_id,
        "title": fetched.get("title") or hit.get("title") or hit.get("url", ""),
        "source": hit.get("source") or _domain_from_url(hit.get("url", "")),
        "url": hit.get("url", ""),
        "published_at": fetched.get("published_at"),
        "snippet": fetched.get("snippet") or hit.get("snippet", ""),
        "content_type": _infer_content_type(hit.get("url", ""), fetched.get("title", "")),
        "entity_id": hit.get("entity_id"),
    }


def _domain_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        return p.netloc or ""
    except Exception:
        return ""


def _infer_content_type(url: str, title: str) -> str:
    u = (url + " " + title).lower()
    if "press-release" in u or "prnewswire" in u or "businesswire" in u or "press release" in u:
        return "press_release"
    if "blog" in u:
        return "blog"
    if "news" in u or "reuters" in u or "apnews" in u:
        return "news"
    return "other"
