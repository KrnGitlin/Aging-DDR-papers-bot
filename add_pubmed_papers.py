#!/usr/bin/env python3
"""Simple test to update papers.json with only PubMed papers"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta, timezone
import yaml
from scipaperbot.fetchers.pubmed import fetch_pubmed
from scripts.update_papers import match_keywords
from scipaperbot.storage import save_papers, load_papers
from scipaperbot.models import Paper

def main():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    keywords = config.get('keywords', [])
    site_data_path = Path(config.get("site_data_path", "site/data/papers.json"))
    
    # Date range
    now = datetime.now(timezone.utc).astimezone(tz=None).replace(tzinfo=None)
    cutoff = now - timedelta(days=2)
    start_str = cutoff.strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")
    
    print(f"Fetching PubMed papers from {start_str} to {end_str}")
    print(f"Keywords: {keywords}")
    
    # Load existing papers
    try:
        existing_papers = load_papers(site_data_path)
        print(f"Loaded {len(existing_papers)} existing papers")
    except:
        existing_papers = []
        print("No existing papers found")
    
    # Fetch PubMed papers
    pub_email = config.get("pubmed", {}).get("email", "test@example.com")
    
    try:
        fetched = fetch_pubmed(
            keywords=keywords, 
            start_date=start_str, 
            end_date=end_str, 
            max_results=50, 
            email=pub_email
        )
        print(f"Fetched {len(fetched)} papers from PubMed")
        
        # Process and filter
        pubmed_papers = []
        for p in fetched:
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                if hits:
                    p.matched_keywords = hits
                    pubmed_papers.append(p)
                    print(f"✓ {p.title[:80]}... [{', '.join(hits)}]")
        
        print(f"Found {len(pubmed_papers)} matching PubMed papers")
        
        # Combine with existing papers (remove old PubMed papers first)
        non_pubmed_papers = [p for p in existing_papers if p.source != "PubMed"]
        all_papers = non_pubmed_papers + pubmed_papers
        
        # Save
        save_papers(site_data_path, all_papers)
        print(f"Saved {len(all_papers)} total papers to {site_data_path}")
        
        return len(pubmed_papers)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    main()