from __future__ import annotations

import requests
from datetime import datetime
from typing import List

from scipaperbot.models import Paper

API_BASE = "https://api.biorxiv.org"  # supports both biorxiv and medrxiv


def _parse_item(it: dict, source_name: str) -> Paper:
    doi = it.get("doi")
    title = (it.get("title") or "").strip()
    # authors string: "Last, First; Last, First"
    authors_str = it.get("authors") or ""
    authors = [a.strip() for a in authors_str.split(";") if a.strip()]
    date_str = it.get("date")  # YYYY-MM-DD
    try:
        published = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        published = datetime.utcnow()
    link = f"https://www.biorxiv.org/content/{doi}v1" if source_name == "bioRxiv" else f"https://www.medrxiv.org/content/{doi}v1"
    # Some DOIs in bio/medrxiv are like 10.1101/2024.01.23.12...

    return Paper(
        id=f"doi:{doi}" if doi else link,
        title=title,
        authors=authors,
        summary="",  # API endpoint used does not include abstract; can be added with per-DOI call if needed
        published=published,
        updated=None,
        link=link,
        categories=[],
        source=source_name,
        doi=doi,
        primary_category=None,
    )


def fetch_rxiv(
    server: str,  # 'biorxiv' or 'medrxiv'
    start_date: str,  # YYYY-MM-DD
    end_date: str,  # YYYY-MM-DD
    max_results: int = 100,
) -> List[Paper]:
    assert server in ("biorxiv", "medrxiv")
    url = f"{API_BASE}/details/{server}/{start_date}/{end_date}"
    papers: List[Paper] = []
    cursor = 0
    headers = {"User-Agent": "scipaperbot/0.1 (+https://github.com/)"}

    while len(papers) < max_results:
        page_url = f"{url}/{cursor}"
        resp = requests.get(page_url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("collection", [])
        if not items:
            break
        for it in items:
            papers.append(_parse_item(it, "bioRxiv" if server == "biorxiv" else "medRxiv"))
            if len(papers) >= max_results:
                break
        cursor += 1

    return papers
