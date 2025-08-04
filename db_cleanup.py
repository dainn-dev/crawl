#!/usr/bin/env python3
"""
Database Cleanup Utility
=======================

This script helps you clean up duplicate URLs in the database and check database status.

Usage:
    python db_cleanup.py check          # Check for duplicate URLs
    python db_cleanup.py cleanup        # Clean up duplicate URLs
    python db_cleanup.py status         # Show database status
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.db import check_duplicate_urls, cleanup_duplicate_urls, get_session, CourtCase, normalize_existing_urls
from sqlalchemy import func

def show_database_status():
    """Show database status and statistics"""
    session = get_session()
    try:
        # Total records
        total_records = session.query(CourtCase).count()
        print(f"Total records in database: {total_records}")
        
        # Records by domain
        from urllib.parse import urlparse
        domains = {}
        www_records = []
        for case in session.query(CourtCase).all():
            try:
                domain = urlparse(case.url).netloc
                domains[domain] = domains.get(domain, 0) + 1
                
                # Check for www records
                if domain.startswith('www.'):
                    www_records.append(case.url)
            except:
                pass
        
        print("\nRecords by domain:")
        for domain, count in sorted(domains.items()):
            print(f"  {domain}: {count} records")
        
        if www_records:
            print(f"\nFound {len(www_records)} records with www prefix:")
            for url in www_records[:5]:  # Show first 5
                print(f"  {url}")
            if len(www_records) > 5:
                print(f"  ... and {len(www_records) - 5} more")
        
        # Check for duplicates
        print("\nChecking for duplicates...")
        duplicates = check_duplicate_urls()
        
        if duplicates:
            print(f"\nFound {len(duplicates)} URLs with duplicates that need cleanup")
        else:
            print("\nNo duplicates found - database is clean!")
            
    except Exception as e:
        print(f"Error checking database status: {e}")
    finally:
        session.close()

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Database Cleanup Utility")
        print("=======================")
        print()
        print("Commands:")
        print("  check                    Check for duplicate URLs")
        print("  cleanup                  Clean up duplicate URLs")
        print("  normalize                Normalize URLs (remove www prefixes)")
        print("  status                   Show database status")
        print()
        print("Examples:")
        print("  python db_cleanup.py check")
        print("  python db_cleanup.py cleanup")
        print("  python db_cleanup.py normalize")
        print("  python db_cleanup.py status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "check":
        print("=== Checking for Duplicate URLs ===")
        check_duplicate_urls()
    elif command == "cleanup":
        print("=== Cleaning up Duplicate URLs ===")
        cleanup_duplicate_urls()
    elif command == "normalize":
        print("=== Normalizing URLs ===")
        normalize_existing_urls()
    elif command == "status":
        print("=== Database Status ===")
        show_database_status()
    else:
        print(f"Unknown command: {command}")
        print("Use: check, cleanup, normalize, or status")

if __name__ == "__main__":
    main() 