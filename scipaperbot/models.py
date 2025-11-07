from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class Paper:
    id: str
    title: str
    authors: List[str]
    summary: str
    published: datetime
    updated: Optional[datetime]
    link: str
    categories: List[str]
    source: str = "arXiv"
    doi: Optional[str] = None
    primary_category: Optional[str] = None
    matched_keywords: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["published"] = self.published.strftime(ISO_FMT)
        d["updated"] = self.updated.strftime(ISO_FMT) if self.updated else None
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Paper":
        pub = d.get("published")
        upd = d.get("updated")
        return Paper(
            id=d["id"],
            title=d["title"],
            authors=list(d.get("authors", [])),
            summary=d.get("summary", ""),
            published=datetime.strptime(pub, ISO_FMT) if isinstance(pub, str) else pub,
            updated=datetime.strptime(upd, ISO_FMT) if isinstance(upd, str) and upd else None,
            link=d.get("link", ""),
            categories=list(d.get("categories", [])),
            source=d.get("source", "arXiv"),
            doi=d.get("doi"),
            primary_category=d.get("primary_category"),
            matched_keywords=list(d.get("matched_keywords", [])) if d.get("matched_keywords") else None,
        )
