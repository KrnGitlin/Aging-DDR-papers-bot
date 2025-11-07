from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is importable when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import re

import yaml

from scipaperbot.fetchers.arxiv import fetch_arxiv_papers
from scipaperbot.fetchers.biorxiv import fetch_rxiv
from scipaperbot.fetchers.pubmed import fetch_pubmed
from scipaperbot.fetchers.chemrxiv import fetch_chemrxiv
from scipaperbot.models import Paper
from scipaperbot.storage import save_papers, dedupe_and_sort


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def match_keywords(paper: Paper, keywords: List[str]) -> List[str]:
    """Return keywords matched using biology-oriented, word-boundary aware rules.
    - Uses word boundaries to avoid false positives (e.g., 'PAge' != 'aging').
    - Handles combined phrases like 'DNA damage & Repair' by requiring key tokens.
    - Supports DDR as acronym or 'dna damage response'.
    """
    text = f"{paper.title}\n{paper.summary}"
    text_lower = text.lower()
    words = set(re.findall(r"[a-zA-Z]+", text_lower))

    matches: List[str] = []

    # Pre-compiled patterns
    pat_aging = re.compile(r"\baging\b|\bageing\b|\bsenescent\b|\bsenescence\b", re.I)
    pat_ddr = re.compile(r"\bddr\b|\bdna\s+damage\s+response\b", re.I)
    pat_dna_damage = re.compile(r"\bdna\s+damage\b", re.I)
    pat_repair = re.compile(r"\brepair\b", re.I)

    def has_aging() -> bool:
        return bool(pat_aging.search(text))

    def has_ddr() -> bool:
        return bool(pat_ddr.search(text))

    def has_dna_damage() -> bool:
        return bool(pat_dna_damage.search(text))

    def has_repair() -> bool:
        return bool(pat_repair.search(text))

    for kw in keywords:
        k = kw.strip()
        kl = k.lower()
        if not k:
            continue

        if kl in {"ageing", "aging"}:
            if has_aging():
                matches.append(kw)
            continue

        if kl in {"ddr", "dna damage response"}:
            if has_ddr():
                matches.append(kw)
            continue

        if kl in {"dna damage", "damage repair"}:
            # Require presence of key tokens
            if has_dna_damage() or ("dna" in words and has_repair()):
                matches.append(kw)
            continue

        if "dna damage" in kl and "repair" in kl:
            # For 'DNA damage and Repair' / 'DNA damage & Repair'
            if has_dna_damage() and has_repair():
                matches.append(kw)
            continue

        # Default: whole-phrase word-boundary match
        pat = re.compile(r"\b" + re.escape(kl) + r"\b", re.I)
        if pat.search(text):
            matches.append(kw)

    return matches


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Fetch and update papers JSON for the site.")
    ap.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    ap.add_argument("--days", type=int, default=None, help="Override days_back")
    ap.add_argument("--max-results", type=int, default=None, help="Override max_results per keyword")
    ap.add_argument("--write", action="store_true", help="Write outputs to site/data/papers.json")
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config))
    keywords = cfg.get("keywords", [])
    categories = cfg.get("categories", [])
    days_back = args.days if args.days is not None else int(cfg.get("days_back", 7))
    max_results = args.max_results if args.max_results is not None else int(cfg.get("max_results", 100))
    site_data_path = Path(cfg.get("site_data_path", "site/data/papers.json"))

    print(f"Fetching papers for {len(keywords)} keywords, days_back={days_back}...")

    all_papers: List[Paper] = []

    # Date range strings
    now = datetime.now(timezone.utc).astimezone(tz=None).replace(tzinfo=None)
    cutoff = now - timedelta(days=days_back)
    start_str = cutoff.strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")

    sources_cfg = cfg.get("sources", {})
    bio_only = bool(cfg.get("bio_only", True))
    include_arxiv = bool(sources_cfg.get("arxiv", True))
    include_bio = bool(sources_cfg.get("biorxiv", False))
    include_med = bool(sources_cfg.get("medrxiv", False))
    include_pub = bool(sources_cfg.get("pubmed", False))
    include_chem = bool(sources_cfg.get("chemrxiv", False))

    if include_arxiv:
        fetched = fetch_arxiv_papers(keywords=keywords, categories=categories, max_results=max_results)
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    p.matched_keywords = hits
                    all_papers.append(p)

    if include_bio:
        fetched = fetch_rxiv("biorxiv", start_str, end_str, max_results=max_results)
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    p.matched_keywords = hits
                    all_papers.append(p)

    if include_med:
        fetched = fetch_rxiv("medrxiv", start_str, end_str, max_results=max_results)
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    p.matched_keywords = hits
                    all_papers.append(p)

    if include_pub:
        pub_email = (cfg.get("pubmed", {}) or {}).get("email")
        fetched = fetch_pubmed(keywords=keywords, start_date=start_str, end_date=end_str, max_results=max_results, email=pub_email)
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    p.matched_keywords = hits
                    all_papers.append(p)

    if include_chem:
        fetched = fetch_chemrxiv(keywords=keywords, start_date=start_str, end_date=end_str, max_results=max_results)
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    # Optional biology context gate for ChemRxiv
                    if not bio_only or _is_bio_context(p.title + "\n" + p.summary):
                        p.matched_keywords = hits
                        all_papers.append(p)

def _is_bio_context(text: str) -> bool:
    """Heuristic: require at least one biological token in text."""
    bio_tokens = {
        "dna", "rna", "protein", "proteins", "gene", "genes", "genome", "genomic", "genetics",
        "cell", "cells", "cellular", "tissue", "organism", "mouse", "mice", "human", "yeast", "bacteria",
        "mitochondria", "chromatin", "chromosome", "repair", "biological",
    }
    text_l = text.lower()
    words = set(re.findall(r"[a-zA-Z]+", text_l))
    return any(tok in words for tok in bio_tokens)

    # Dedupe + sort, then keep only those that matched at least one keyword
    final = [p for p in dedupe_and_sort(all_papers) if p.matched_keywords]

    print(f"Collected {len(final)} papers across sources within last {days_back} days.")

    if args.write:
        save_papers(site_data_path, final)
        print(f"Wrote {len(final)} papers -> {site_data_path}")
    else:
        # Dry-run summary
        for p in final[:10]:
            print(f"- {p.published.date()} | {p.title[:100]}...")
        if len(final) > 10:
            print(f"... and {len(final) - 10} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
