#!/usr/bin/env python3
"""
Database Sync Utility
====================

This script helps sync database URLs with crawl progress and check existing URLs
to avoid re-crawling already processed URLs.

Usage:
    python db_sync_util.py check <domain>          # Check existing URLs for domain
    python db_sync_util.py sync <domain>           # Sync database URLs to progress
    python db_sync_util.py stats <domain>          # Show domain statistics
    python db_sync_util.py clear_progress          # Clear crawl progress
"""

import sys
import os
import json
from urllib.parse import urlparse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.db import get_existing_urls_for_domain, get_domain_stats_from_db, get_session, CourtCase
from crawler.crawler import save_progress, load_progress, clear_progress

def check_existing_urls(domain):
    """Check existing URLs for a domain in the database"""
    print(f"=== Checking existing URLs for {domain} ===")
    
    existing_urls = get_existing_urls_for_domain(domain)
    
    if not existing_urls:
        print(f"No existing URLs found for {domain}")
        return
    
    print(f"Found {len(existing_urls):,} existing URLs for {domain}")
    print()
    
    # Show first 10 URLs as examples
    print("Sample URLs:")
    for i, url in enumerate(sorted(existing_urls)[:10]):
        print(f"  {i+1}. {url}")
    
    if len(existing_urls) > 10:
        print(f"  ... and {len(existing_urls) - 10} more URLs")
    
    print()
    
    # Get domain statistics
    stats = get_domain_stats_from_db(domain)
    print(f"Domain Statistics:")
    print(f"  Total URLs: {stats['total_urls']:,}")
    print(f"  Successful: {stats['successful_urls']:,} ({stats['success_rate']:.1f}%)")
    print(f"  Failed: {stats['failed_urls']:,}")
    
    # Show status code breakdown
    if stats['status_codes']:
        print(f"  Status Codes:")
        for status_code, count in sorted(stats['status_codes'].items()):
            percentage = (count / stats['total_urls'] * 100) if stats['total_urls'] > 0 else 0
            print(f"    {status_code}: {count:,} ({percentage:.1f}%)")

def sync_database_to_progress(domain):
    """Sync existing database URLs to crawl progress"""
    print(f"=== Syncing database URLs to progress for {domain} ===")
    
    # Get existing URLs from database
    existing_urls = get_existing_urls_for_domain(domain)
    
    if not existing_urls:
        print(f"No existing URLs found for {domain}")
        return
    
    # Load current progress
    current_progress, current_depth = load_progress(domain)
    
    # Merge database URLs with current progress
    merged_urls = current_progress.union(existing_urls)
    
    print(f"Current progress URLs: {len(current_progress):,}")
    print(f"Database URLs: {len(existing_urls):,}")
    print(f"Merged URLs: {len(merged_urls):,}")
    
    # Save merged progress
    save_progress(domain, merged_urls, current_depth)
    
    print(f"✅ Progress synced! {len(merged_urls):,} URLs now in progress file")
    
    # Show what was added
    new_urls = existing_urls - current_progress
    if new_urls:
        print(f"Added {len(new_urls):,} new URLs from database to progress")
    else:
        print("No new URLs added (all were already in progress)")

def show_domain_stats(domain):
    """Show detailed statistics for a domain"""
    print(f"=== Domain Statistics for {domain} ===")
    
    # Get database statistics
    db_stats = get_domain_stats_from_db(domain)
    
    # Get progress statistics
    progress_urls, progress_depth = load_progress(domain)
    
    print(f"📊 DATABASE STATISTICS:")
    print(f"   Total URLs: {db_stats['total_urls']:,}")
    print(f"   Successful: {db_stats['successful_urls']:,} ({db_stats['success_rate']:.1f}%)")
    print(f"   Failed: {db_stats['failed_urls']:,}")
    print()
    
    print(f"📈 PROGRESS STATISTICS:")
    print(f"   URLs in progress: {len(progress_urls):,}")
    print(f"   Current depth: {progress_depth}")
    print()
    
    # Show overlap
    existing_urls = get_existing_urls_for_domain(domain)
    overlap = existing_urls.intersection(progress_urls)
    
    print(f"🔄 OVERLAP ANALYSIS:")
    print(f"   Database URLs: {len(existing_urls):,}")
    print(f"   Progress URLs: {len(progress_urls):,}")
    print(f"   Overlapping URLs: {len(overlap):,}")
    print(f"   URLs only in DB: {len(existing_urls - progress_urls):,}")
    print(f"   URLs only in progress: {len(progress_urls - existing_urls):,}")
    
    # Show status code breakdown
    if db_stats['status_codes']:
        print()
        print(f"📋 STATUS CODE BREAKDOWN:")
        for status_code, count in sorted(db_stats['status_codes'].items()):
            percentage = (count / db_stats['total_urls'] * 100) if db_stats['total_urls'] > 0 else 0
            print(f"   {status_code}: {count:,} ({percentage:.1f}%)")

def clear_progress_command():
    """Clear all crawl progress"""
    print("=== Clearing all crawl progress ===")
    
    # Clear progress files
    clear_progress()
    
    print("✅ All crawl progress cleared")
    print("Note: Database URLs remain intact")

def show_help():
    """Show help information"""
    print("Database Sync Utility")
    print("====================")
    print()
    print("Commands:")
    print("  check <domain>              Check existing URLs for domain")
    print("  sync <domain>               Sync database URLs to progress")
    print("  stats <domain>              Show domain statistics")
    print("  clear_progress              Clear all crawl progress")
    print("  help                        Show this help message")
    print()
    print("Examples:")
    print("  python db_sync_util.py check cylaw.org")
    print("  python db_sync_util.py sync eur-lex.europa.eu")
    print("  python db_sync_util.py stats cylaw.org")
    print("  python db_sync_util.py clear_progress")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "check":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python db_sync_util.py check cylaw.org")
            return
        domain = sys.argv[2]
        check_existing_urls(domain)
    elif command == "sync":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python db_sync_util.py sync cylaw.org")
            return
        domain = sys.argv[2]
        sync_database_to_progress(domain)
    elif command == "stats":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python db_sync_util.py stats cylaw.org")
            return
        domain = sys.argv[2]
        show_domain_stats(domain)
    elif command == "clear_progress":
        clear_progress_command()
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        print()
        show_help()

if __name__ == "__main__":
    main() 