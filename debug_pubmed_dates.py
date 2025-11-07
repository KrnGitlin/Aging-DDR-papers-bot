#!/usr/bin/env python3
"""Debug PubMed date parsing"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
from datetime import datetime

def debug_pubmed_data():
    EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search for recent papers
    params = {
        "db": "pubmed",
        "term": "aging[Title/Abstract]",
        "retmode": "json",
        "retmax": "3",
        "sort": "pub+date",
        "mindate": "2025-11-04",
        "maxdate": "2025-11-07",
        "datetype": "pdat",
        "tool": "debug",
        "email": "test@example.com",
    }
    
    print("Searching PubMed...")
    r = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    search_result = r.json()
    print(f"Search result: {search_result}")
    
    ids = search_result.get("esearchresult", {}).get("idlist", [])
    print(f"Found IDs: {ids}")
    
    if not ids:
        print("No papers found")
        return
    
    # Get details
    params2 = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
        "tool": "debug", 
        "email": "test@example.com",
    }
    
    print("Getting paper details...")
    r2 = requests.get(f"{EUTILS}/esummary.fcgi", params=params2, timeout=30)
    r2.raise_for_status()
    data = r2.json()
    
    print(f"Summary data keys: {list(data.keys())}")
    result = data.get("result", {})
    print(f"Result keys: {list(result.keys())}")
    
    for pmid in ids[:2]:  # Just check first 2
        rec = result.get(pmid)
        if rec:
            print(f"\nPMID {pmid}:")
            print(f"  Title: {rec.get('title', 'NO TITLE')}")
            print(f"  Raw pubdate: '{rec.get('pubdate', 'NO PUBDATE')}'")
            print(f"  Raw sortpubdate: '{rec.get('sortpubdate', 'NO SORTPUBDATE')}'")
            print(f"  Raw epubdate: '{rec.get('epubdate', 'NO EPUBDATE')}'")
            print(f"  All date-related keys: {[k for k in rec.keys() if 'date' in k.lower()]}")
            
            # Test current parsing logic
            pubdate = (rec.get("pubdate") or "").split()[0] if rec.get("pubdate") else ""
            print(f"  Parsed pubdate (first word): '{pubdate}'")
            
            # Try to parse with current logic
            dt = None
            for fmt in ("%Y %b %d", "%Y %b", "%Y"):
                try:
                    dt = datetime.strptime(pubdate, fmt)
                    print(f"  Parsed with format '{fmt}': {dt}")
                    break
                except Exception as e:
                    print(f"  Failed with format '{fmt}': {e}")

if __name__ == "__main__":
    debug_pubmed_data()