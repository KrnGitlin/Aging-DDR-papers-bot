#!/usr/bin/env python3
"""Test script to debug PubMed paper fetching and processing"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta, timezone
import yaml
from scipaperbot.fetchers.pubmed import fetch_pubmed
from scripts.update_papers import match_keywords

def main():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    keywords = config.get('keywords', [])
    print(f"Keywords: {keywords}")
    
    # Date range
    now = datetime.now(timezone.utc).astimezone(tz=None).replace(tzinfo=None)
    cutoff = now - timedelta(days=3)
    start_str = cutoff.strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")
    
    print(f"Fetching PubMed papers from {start_str} to {end_str}")
    
    # Fetch PubMed papers
    pub_email = config.get("pubmed", {}).get("email", "test@example.com")
    print(f"Using email: {pub_email}")
    
    try:
        fetched = fetch_pubmed(
            keywords=keywords, 
            start_date=start_str, 
            end_date=end_str, 
            max_results=20, 
            email=pub_email
        )
        print(f"Fetched {len(fetched)} papers from PubMed")
        
        matched_papers = []
        for i, p in enumerate(fetched):
            print(f"\n{i+1}. Paper: {p.title}")
            print(f"   Published: {p.published}")
            print(f"   Cutoff: {cutoff}")
            print(f"   Published >= cutoff: {p.published >= cutoff}")
            
            if p.published >= cutoff:
                hits = match_keywords(p, keywords)
                text_sample = f"{p.title}\n{p.summary}".lower()[:200]
                print(f"   Text sample: {text_sample}")
                
                if hits:
                    p.matched_keywords = hits
                    matched_papers.append(p)
                    print(f"   ✓ MATCHED with keywords: {hits}")
                else:
                    print(f"   ✗ No keyword match")
            else:
                print(f"   ✗ Too old (published before cutoff)")
        
        print(f"\nFinal result: {len(matched_papers)} PubMed papers matched keywords")
        
        return matched_papers
        
    except Exception as e:
        print(f"Error fetching PubMed papers: {e}")
        return []

if __name__ == "__main__":
    main()