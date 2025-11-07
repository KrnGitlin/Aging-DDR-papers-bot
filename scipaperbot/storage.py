from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from scipaperbot.models import Paper


def load_papers(path: str | Path) -> List[Paper]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "papers" in data:
        items = data["papers"]
    else:
        items = data
    return [Paper.from_dict(d) for d in items]


def save_papers(path: str | Path, papers: List[Paper]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump([paper.to_dict() for paper in papers], f, ensure_ascii=False, indent=2)


def dedupe_and_sort(papers: List[Paper]) -> List[Paper]:
    seen: Dict[str, Paper] = {}
    for paper in papers:
        # Keep the newest occurrence by published date
        if paper.id not in seen or seen[paper.id].published < paper.published:
            seen[paper.id] = paper
    result = list(seen.values())
    result.sort(key=lambda p: p.published, reverse=True)
    return result
