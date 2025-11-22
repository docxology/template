#!/usr/bin/env python3
"""Wrapper script for literature search."""
import argparse
import sys
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from infrastructure.literature import LiteratureSearch, LiteratureConfig

def main():
    parser = argparse.ArgumentParser(description="Search scientific literature.")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--download", action="store_true", help="Download PDFs")
    
    args = parser.parse_args()
    
    config = LiteratureConfig()
    searcher = LiteratureSearch(config)
    
    print(f"Searching for: {args.query}...")
    results = searcher.search(args.query, limit=args.limit)
    
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors)}")
        print(f"   Year: {paper.year}")
        if paper.doi:
            print(f"   DOI: {paper.doi}")
            
        searcher.add_to_library(paper)
        
        if args.download and paper.pdf_url:
            path = searcher.download_paper(paper)
            if path:
                print(f"   Downloaded to: {path}")

if __name__ == "__main__":
    main()

