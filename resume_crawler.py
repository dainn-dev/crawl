#!/usr/bin/env python3
"""
Crawl Resume Utility
===================

This script helps you manage crawl progress and resume crawling from where you left off.

Usage:
    python resume_crawler.py status          # Show current progress
    python resume_crawler.py resume         # Resume crawling
    python resume_crawler.py clear          # Clear all progress
    python resume_crawler.py clear <domain> # Clear progress for specific domain
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.crawler import get_progress_summary, clear_progress, load_progress
from crawler.main import run_hybrid_parallel_crawl, run_resume_crawl
from crawler.config import TARGET_SITES

def show_status():
    """Show current crawl progress"""
    print("=== Crawl Progress Status ===")
    print()
    
    summary = get_progress_summary()
    
    if not summary:
        print("No saved progress found.")
        return
    
    total_urls = 0
    for domain, data in summary.items():
        urls_crawled = data['urls_crawled']
        current_depth = data['current_depth']
        last_updated = data['last_updated']
        
        print(f"Domain: {domain}")
        print(f"  URLs Crawled: {urls_crawled}")
        print(f"  Current Depth: {current_depth}")
        print(f"  Last Updated: {last_updated}")
        print()
        
        total_urls += urls_crawled
    
    print(f"Total URLs crawled across all domains: {total_urls}")

def resume_crawling():
    """Resume crawling from saved progress"""
    print("=== Resuming Crawl ===")
    print()
    
    summary = get_progress_summary()
    
    if not summary:
        print("No saved progress found. Starting fresh crawl...")
        run_hybrid_parallel_crawl(max_depth=3, sites=TARGET_SITES[:2])
        return
    
    print("Found saved progress:")
    for domain, data in summary.items():
        print(f"  {domain}: {data['urls_crawled']} URLs at depth {data['current_depth']}")
    
    print()
    print("Resuming crawl with saved progress...")
    print("The crawler will skip already crawled URLs and continue from where it left off.")
    print()
    
    # Resume crawling
    run_resume_crawl(max_depth=3, sites=TARGET_SITES[:2])

def clear_progress_command(domain=None):
    """Clear crawl progress"""
    if domain:
        clear_progress(domain)
        print(f"Cleared progress for domain: {domain}")
    else:
        clear_progress()
        print("Cleared all crawl progress")

def show_help():
    """Show help information"""
    print("Crawl Resume Utility")
    print("===================")
    print()
    print("Commands:")
    print("  status                    Show current crawl progress")
    print("  resume                    Resume crawling from saved progress")
    print("  clear                     Clear all progress")
    print("  clear <domain>            Clear progress for specific domain")
    print("  help                      Show this help message")
    print()
    print("Examples:")
    print("  python resume_crawler.py status")
    print("  python resume_crawler.py resume")
    print("  python resume_crawler.py clear")
    print("  python resume_crawler.py clear eur-lex.europa.eu")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "resume":
        resume_crawling()
    elif command == "clear":
        if len(sys.argv) > 2:
            domain = sys.argv[2]
            clear_progress_command(domain)
        else:
            clear_progress_command()
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        print()
        show_help()

if __name__ == "__main__":
    main() 