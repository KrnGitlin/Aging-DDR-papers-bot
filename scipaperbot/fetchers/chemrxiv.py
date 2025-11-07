from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

import requests

from scipaperbot.models import Paper

CROSSREF = "https://api.crossref.org/works"
CHEMRXIV_PREFIX = "10.26434"  # DOI prefix for ChemRxiv


def fetch_chemrxiv(
    keywords: Iterable[str],
    start_date: str,  # YYYY-MM-DD
    end_date: str,  # YYYY-MM-DD
    max_results: int = 100,
) -> List[Paper]:
    headers = {"User-Agent": "scipaperbot/0.1 (+https://github.com/)"}
    papers: List[Paper] = []
    for kw in keywords:
        if len(papers) >= max_results:
            break
        params = {
            "rows": str(max(1, min(100, max_results - len(papers)))) ,
            "query": kw,
            "filter": f"from-pub-date:{start_date},until-pub-date:{end_date},prefix:{CHEMRXIV_PREFIX}",
            "sort": "published",
            "order": "desc",
        }
        r = requests.get(CROSSREF, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        for it in items:
            doi = it.get("DOI")
            title_list = it.get("title", [])
            title = (title_list[0] if title_list else "").strip()
            authors = []
            for a in it.get("author", []) or []:
                given = a.get("given") or ""
                family = a.get("family") or ""
                nm = (given + " " + family).strip()
                if nm:
                    authors.append(nm)
            # published date parts
            dt = datetime.utcnow()
            for fld in ("published-print", "published-online", "created", "deposited"):
                if it.get(fld, {}).get("date-parts"):
                    ymd = it[fld]["date-parts"][0]
                    # date-parts may be [YYYY, M, D]
                    try:
                        y = ymd[0]; m = ymd[1] if len(ymd) > 1 else 1; d = ymd[2] if len(ymd) > 2 else 1
                        dt = datetime(int(y), int(m), int(d))
                        break
                    except Exception:
                        pass
            url = it.get("URL") or (f"https://doi.org/{doi}" if doi else "")
            papers.append(
                Paper(
                    id=f"doi:{doi}" if doi else url,
                    title=title,
                    authors=authors,
                    summary="",
                    published=dt,
                    updated=None,
                    link=url,
                    categories=[],
                    source="ChemRxiv",
                    doi=doi,
                )
            )
            if len(papers) >= max_results:
                break
    return papers
