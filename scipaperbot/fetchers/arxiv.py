from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import quote_plus
import requests

import feedparser

from scipaperbot.models import Paper


# Build a search query string for arXiv API
# arXiv query docs: https://info.arxiv.org/help/api/user-manual.html
# We'll search in title and abstract for keywords, and optionally filter by categories.

def _build_query(keywords: Iterable[str], categories: Optional[Iterable[str]] = None) -> str:
    def qval(s: str) -> str:
        s = s.strip()
        # Quote if contains any non-alphanumeric character
        return f'"{s}"' if re.search(r"[^A-Za-z0-9]", s) else s

    kw_terms = []
    for kw in keywords:
        term = kw.strip()
        if not term:
            continue
        v = qval(term)
        kw_terms.append(f"ti:{v} OR abs:{v}")
    kw_part = " OR ".join(kw_terms) if kw_terms else "all:ai"

    cat_terms = []
    if categories:
        for cat in categories:
            c = cat.strip()
            if c:
                cat_terms.append(f"cat:{c}")
    cat_part = " OR ".join(cat_terms)

    if cat_part:
        return f"({kw_part}) AND ({cat_part})"
    return kw_part


def fetch_arxiv_papers(
    keywords: Iterable[str],
    categories: Optional[Iterable[str]] = None,
    max_results: int = 100,
) -> List[Paper]:
    """
    Fetch papers from arXiv matching keywords/categories.
    Note: arXiv API doesn't support arbitrary date range filters; filter dates client-side.
    """
    query = _build_query(keywords, categories)
    base_url = "https://export.arxiv.org/api/query"
    # Fetch more than needed if possible; caller should filter by date later
    max_results = max(1, min(300, max_results))
    enc_query = quote_plus(query)
    url = (
        f"{base_url}?search_query={enc_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )

    headers = {"User-Agent": "scipaperbot/0.1 (+https://github.com/)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    papers: List[Paper] = []

    for entry in feed.entries:
        # arXiv id may appear as 'http://arxiv.org/abs/xxxx.yyyyv1'
        arxiv_id = entry.get("id", "")
        link = ""
        for l in entry.get("links", []):
            if l.get("rel") == "alternate":
                link = l.get("href")
                break
        if not link:
            link = entry.get("link", arxiv_id)

        # parse authors
        authors = [a.get("name") for a in entry.get("authors", []) if a.get("name")]
        # categories
        categories = [t.get("term") for t in entry.get("tags", []) if t.get("term")]

        published_str = entry.get("published")
        updated_str = entry.get("updated")
        # arXiv uses RFC3339 / ISO strings; feedparser converts to struct_time too, but keep robust
        def to_dt(s: Optional[str]) -> Optional[datetime]:
            if not s:
                return None
            # Try feedparser's parsed date
            if entry.get("published_parsed") and s == published_str:
                try:
                    import time

                    return datetime.utcfromtimestamp(time.mktime(entry.published_parsed))
                except Exception:
                    pass
            try:
                # Remove timezone if present
                s2 = re.sub(r"[+-]\d{2}:?\d{2}$", "Z", s)
                return datetime.fromisoformat(s2.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                return None

        published = to_dt(published_str)
        updated = to_dt(updated_str)

        paper = Paper(
            id=arxiv_id,
            title=entry.get("title", "").strip(),
            authors=authors,
            summary=entry.get("summary", "").strip(),
            published=published if published else datetime.utcnow(),
            updated=updated,
            link=link,
            categories=categories,
            source="arXiv",
            doi=entry.get("arxiv_doi") if hasattr(entry, "arxiv_doi") else None,
            primary_category=entry.get("arxiv_primary_category", {}).get("term")
            if hasattr(entry, "arxiv_primary_category")
            else None,
        )
        papers.append(paper)

    return papers
