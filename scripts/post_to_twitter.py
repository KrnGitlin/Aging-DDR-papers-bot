from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is importable when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from scipaperbot.models import Paper
from scipaperbot.storage import load_papers
from scipaperbot.twitter import TwitterClient
from scipaperbot.fetchers.biorxiv import fetch_rxiv
from datetime import datetime, timedelta, timezone


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_posted(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data)
        except Exception:
            return set()


def save_posted(path: Path, ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(sorted(list(ids)), f, ensure_ascii=False, indent=2)


def compose_tweet(p: Paper, hashtags: List[str]) -> str:
    # Keep it short: Title + link + tags (prefer <= 3 tags)
    base = p.title.strip()
    url = p.link
    tags = [f"#{t}" for t in hashtags[:2]]  # cap fixed tags to 2
    if p.matched_keywords:
        # include at most one keyword as hashtag, if not already present
        k = p.matched_keywords[0].replace(" ", "")
        if f"#{k}".lower() not in [t.lower() for t in tags]:
            tags.append(f"#{k}")
    tail = " ".join(tags)
    # Ensure within 280 chars
    remaining = 280 - len(tail) - len(url) - 2  # spaces
    title = base if len(base) <= remaining else (base[: max(0, remaining - 3)] + "...")
    return f"{title} {url} {tail}".strip()


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Post recent papers to Twitter (X)")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max", type=int, default=None, help="Max tweets to post")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--source",
        action="append",
        default=None,
        help="Only include papers from this source (e.g., bioRxiv). Can be repeated.",
    )
    ap.add_argument(
        "--live-biorxiv",
        action="store_true",
        help="Fetch bioRxiv live for the given --days window instead of using site data.",
    )
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config))
    site_data_path = Path(cfg.get("site_data_path", "site/data/papers.json"))
    twitter_cfg = cfg.get("twitter", {})
    hashtags = twitter_cfg.get("hashtags", ["arXiv", "AI"])
    max_posts = args.max if args.max is not None else int(twitter_cfg.get("max_posts", 5))
    enabled = bool(twitter_cfg.get("enabled", False))
    dry_run = args.dry_run or bool(twitter_cfg.get("dry_run", True))

    now = datetime.now(timezone.utc).astimezone(tz=None).replace(tzinfo=None)
    cutoff = now - timedelta(days=int(args.days))

    if args.live_biorxiv:
        start_str = (now - timedelta(days=int(args.days))).strftime("%Y-%m-%d")
        end_str = now.strftime("%Y-%m-%d")
        fetched = fetch_rxiv("biorxiv", start_str, end_str, max_results=200)
        papers = []
        for p in fetched:
            if p.published >= cutoff:
                # Minimal keyword check: reuse matched_keywords if present in site, else infer from title only
                text = f"{p.title}\n{p.summary}".lower()
                # heuristic: check simple tokens to avoid importing update logic
                keys = ["ageing","aging","dna damage","ddr","damage repair","dna damage and repair","dna damage & repair"]
                hits = [k for k in keys if k in text]
                if hits:
                    p.matched_keywords = hits
                    papers.append(p)
    else:
        papers = load_papers(site_data_path)

    recent = [p for p in papers if p.published >= cutoff]
    if args.source:
        srcset = set([s.lower() for s in args.source])
        recent = [p for p in recent if (p.source or "").lower() in srcset]

    posted_path = Path("data/posted_ids.json")
    posted = load_posted(posted_path)

    to_post = [p for p in recent if p.id not in posted][:max_posts]

    if not to_post:
        print("Nothing new to post.")
        return 0

    if dry_run or not enabled:
        print("Dry-run or disabled. Tweets that would be posted:")
        for p in to_post:
            print("-", compose_tweet(p, hashtags))
        return 0

    client = TwitterClient()
    who = client.verify()
    print(f"Authenticated as @{who}")

    for p in to_post:
        text = compose_tweet(p, hashtags)
        client.post(text)
        posted.add(p.id)
        print("Posted:", text)

    save_posted(posted_path, posted)
    print(f"Saved posted IDs -> {posted_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
