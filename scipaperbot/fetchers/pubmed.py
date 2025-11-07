from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable, List, Optional

import requests

from scipaperbot.models import Paper

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _build_term(keywords: Iterable[str]) -> str:
    terms = []
    for kw in keywords:
        k = kw.strip()
        if not k:
            continue
        if any(ch for ch in k if not ch.isalnum()):
            k = f'"{k}"'
        terms.append(f"{k}[Title/Abstract]")
    return " OR ".join(terms) if terms else "aging[Title/Abstract]"


def fetch_pubmed(
    keywords: Iterable[str],
    start_date: str,  # YYYY-MM-DD
    end_date: str,  # YYYY-MM-DD
    max_results: int = 100,
    email: Optional[str] = None,
) -> List[Paper]:
    tool = "scipaperbot"
    email = email or os.getenv("PUBMED_EMAIL") or "you@example.com"
    term = _build_term(keywords)

    # ESearch to get PMIDs
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(max_results),
        "sort": "pub+date",
        "mindate": start_date,
        "maxdate": end_date,
        "datetype": "pdat",
        "tool": tool,
        "email": email,
    }
    r = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # ESummary to get details
    params2 = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
        "tool": tool,
        "email": email,
    }
    r2 = requests.get(f"{EUTILS}/esummary.fcgi", params=params2, timeout=30)
    r2.raise_for_status()
    data = r2.json()
    result = data.get("result", {})

    papers: List[Paper] = []
    for pmid in ids:
        rec = result.get(pmid)
        if not rec:
            continue
        title = (rec.get("title") or "").strip()
        authors = [a.get("name") for a in rec.get("authors", []) if a.get("name")]
        pubdate = (rec.get("pubdate") or "").strip()  # often '2025 Nov 6'
        # Try to parse pubdate leniently
        dt = None
        for fmt in ("%Y %b %d", "%Y %b", "%Y"):
            try:
                dt = datetime.strptime(pubdate, fmt)
                break
            except Exception:
                continue
        if not dt:
            try:
                dt = datetime.strptime(pubdate, "%Y-%m-%d")
            except Exception:
                dt = datetime.utcnow()
        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        papers.append(
            Paper(
                id=f"PMID:{pmid}",
                title=title,
                authors=authors,
                summary="",  # ESummary doesn’t return abstract
                published=dt,
                updated=None,
                link=link,
                categories=[],
                source="PubMed",
                doi=None,
            )
        )
    return papers
