#!/usr/bin/env python3
"""
Crawl Coverage Analyzer
=======================

This tool analyzes crawl coverage to determine if crawl_progress.json contains
all URLs from a site by comparing with database records and providing detailed statistics.

Usage:
    python crawl_coverage_analyzer.py analyze <domain>     # Full coverage analysis
    python crawl_coverage_analyzer.py compare <domain>     # Compare progress vs database
    python crawl_coverage_analyzer.py missing <domain>     # Show missing URLs
    python crawl_coverage_analyzer.py stats <domain>       # Coverage statistics
"""

import sys
import os
import json
from urllib.parse import urlparse
from collections import defaultdict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.db import get_existing_urls_for_domain, get_domain_stats_from_db, get_session, CourtCase
from crawler.crawler import load_progress, save_progress

def analyze_coverage(domain):
    """Comprehensive coverage analysis for a domain"""
    print(f"=== COMPREHENSIVE COVERAGE ANALYSIS FOR {domain} ===")
    print()
    
    # Get database URLs
    db_urls = get_existing_urls_for_domain(domain)
    db_stats = get_domain_stats_from_db(domain)
    
    # Get progress URLs
    progress_urls, progress_depth = load_progress(domain)
    
    # Calculate coverage metrics
    total_db_urls = len(db_urls)
    total_progress_urls = len(progress_urls)
    overlapping_urls = db_urls.intersection(progress_urls)
    missing_in_progress = db_urls - progress_urls
    extra_in_progress = progress_urls - db_urls
    
    # Coverage percentage
    coverage_percentage = (len(overlapping_urls) / total_db_urls * 100) if total_db_urls > 0 else 0
    
    print(f"📊 COVERAGE SUMMARY:")
    print(f"   Database URLs: {total_db_urls:,}")
    print(f"   Progress URLs: {total_progress_urls:,}")
    print(f"   Overlapping URLs: {len(overlapping_urls):,}")
    print(f"   Coverage: {coverage_percentage:.1f}%")
    print()
    
    print(f"📈 MISSING ANALYSIS:")
    print(f"   URLs in DB but not in progress: {len(missing_in_progress):,}")
    print(f"   URLs in progress but not in DB: {len(extra_in_progress):,}")
    print()
    
    # Determine if coverage is complete
    if coverage_percentage >= 99.5:
        status = "✅ EXCELLENT COVERAGE"
        recommendation = "Progress file contains virtually all database URLs"
    elif coverage_percentage >= 95:
        status = "⚠️  GOOD COVERAGE"
        recommendation = "Most URLs are covered, but some may be missing"
    elif coverage_percentage >= 80:
        status = "⚠️  MODERATE COVERAGE"
        recommendation = "Significant number of URLs missing from progress"
    else:
        status = "❌ POOR COVERAGE"
        recommendation = "Many URLs missing from progress file"
    
    print(f"🎯 COVERAGE STATUS: {status}")
    print(f"💡 RECOMMENDATION: {recommendation}")
    print()
    
    # Show sample missing URLs
    if missing_in_progress:
        print(f"📋 SAMPLE MISSING URLs (first 10):")
        for i, url in enumerate(sorted(missing_in_progress)[:10]):
            print(f"   {i+1}. {url}")
        if len(missing_in_progress) > 10:
            print(f"   ... and {len(missing_in_progress) - 10} more missing URLs")
        print()
    
    # Show sample extra URLs
    if extra_in_progress:
        print(f"📋 SAMPLE EXTRA URLs (first 10):")
        for i, url in enumerate(sorted(extra_in_progress)[:10]):
            print(f"   {i+1}. {url}")
        if len(extra_in_progress) > 10:
            print(f"   ... and {len(extra_in_progress) - 10} more extra URLs")
        print()
    
    # Depth analysis
    print(f"📏 DEPTH ANALYSIS:")
    print(f"   Current progress depth: {progress_depth}")
    print(f"   URLs at current depth: {len([u for u in progress_urls if u.count('/') >= progress_depth]):,}")
    print()
    
    # Status code analysis
    if db_stats['status_codes']:
        print(f"📊 STATUS CODE ANALYSIS:")
        for status_code, count in sorted(db_stats['status_codes'].items()):
            percentage = (count / total_db_urls * 100) if total_db_urls > 0 else 0
            print(f"   {status_code}: {count:,} ({percentage:.1f}%)")
        print()
    
    return {
        'coverage_percentage': coverage_percentage,
        'total_db_urls': total_db_urls,
        'total_progress_urls': total_progress_urls,
        'missing_urls': len(missing_in_progress),
        'extra_urls': len(extra_in_progress),
        'status': status,
        'recommendation': recommendation
    }

def compare_progress_vs_database(domain):
    """Detailed comparison between progress and database"""
    print(f"=== DETAILED COMPARISON: PROGRESS VS DATABASE FOR {domain} ===")
    print()
    
    # Get data
    db_urls = get_existing_urls_for_domain(domain)
    progress_urls, progress_depth = load_progress(domain)
    
    # Analyze URL patterns
    db_patterns = analyze_url_patterns(db_urls)
    progress_patterns = analyze_url_patterns(progress_urls)
    
    print(f"📊 URL PATTERN ANALYSIS:")
    print(f"   Database URL patterns: {len(db_patterns)}")
    print(f"   Progress URL patterns: {len(progress_patterns)}")
    print()
    
    # Show pattern differences
    missing_patterns = db_patterns - progress_patterns
    extra_patterns = progress_patterns - db_patterns
    
    if missing_patterns:
        print(f"🔍 MISSING URL PATTERNS (first 10):")
        for pattern in sorted(missing_patterns)[:10]:
            print(f"   - {pattern}")
        if len(missing_patterns) > 10:
            print(f"   ... and {len(missing_patterns) - 10} more patterns")
        print()
    
    if extra_patterns:
        print(f"🔍 EXTRA URL PATTERNS (first 10):")
        for pattern in sorted(extra_patterns)[:10]:
            print(f"   - {pattern}")
        if len(extra_patterns) > 10:
            print(f"   ... and {len(extra_patterns) - 10} more patterns")
        print()
    
    # Depth distribution
    print(f"📏 DEPTH DISTRIBUTION:")
    db_depth_dist = get_depth_distribution(db_urls)
    progress_depth_dist = get_depth_distribution(progress_urls)
    
    print(f"   Database depth distribution:")
    for depth, count in sorted(db_depth_dist.items()):
        print(f"     Depth {depth}: {count:,} URLs")
    
    print(f"   Progress depth distribution:")
    for depth, count in sorted(progress_depth_dist.items()):
        print(f"     Depth {depth}: {count:,} URLs")
    print()

def show_missing_urls(domain):
    """Show URLs that are in database but missing from progress"""
    print(f"=== MISSING URLS FOR {domain} ===")
    print()
    
    # Get data
    db_urls = get_existing_urls_for_domain(domain)
    progress_urls, _ = load_progress(domain)
    
    missing_urls = db_urls - progress_urls
    
    if not missing_urls:
        print("✅ No missing URLs found!")
        print("All database URLs are present in progress file.")
        return
    
    print(f"❌ Found {len(missing_urls):,} missing URLs")
    print()
    
    # Group by path pattern
    missing_by_pattern = group_urls_by_pattern(missing_urls)
    
    print(f"📋 MISSING URLS BY PATTERN:")
    for pattern, urls in sorted(missing_by_pattern.items()):
        print(f"   Pattern: {pattern}")
        print(f"   Count: {len(urls):,} URLs")
        print(f"   Sample URLs:")
        for url in sorted(urls)[:5]:
            print(f"     - {url}")
        if len(urls) > 5:
            print(f"     ... and {len(urls) - 5} more")
        print()
    
    # Show all missing URLs if not too many
    if len(missing_urls) <= 50:
        print(f"📋 ALL MISSING URLS:")
        for i, url in enumerate(sorted(missing_urls), 1):
            print(f"   {i:2d}. {url}")
    else:
        print(f"📋 FIRST 50 MISSING URLS:")
        for i, url in enumerate(sorted(missing_urls)[:50], 1):
            print(f"   {i:2d}. {url}")
        print(f"   ... and {len(missing_urls) - 50} more")

def show_coverage_stats(domain):
    """Show detailed coverage statistics"""
    print(f"=== COVERAGE STATISTICS FOR {domain} ===")
    print()
    
    # Get data
    db_urls = get_existing_urls_for_domain(domain)
    progress_urls, progress_depth = load_progress(domain)
    db_stats = get_domain_stats_from_db(domain)
    
    # Calculate metrics
    total_db = len(db_urls)
    total_progress = len(progress_urls)
    overlapping = len(db_urls.intersection(progress_urls))
    missing = len(db_urls - progress_urls)
    extra = len(progress_urls - db_urls)
    
    coverage = (overlapping / total_db * 100) if total_db > 0 else 0
    efficiency = (overlapping / total_progress * 100) if total_progress > 0 else 0
    
    print(f"📊 COVERAGE METRICS:")
    print(f"   Total database URLs: {total_db:,}")
    print(f"   Total progress URLs: {total_progress:,}")
    print(f"   Overlapping URLs: {overlapping:,}")
    print(f"   Missing URLs: {missing:,}")
    print(f"   Extra URLs: {extra:,}")
    print()
    
    print(f"📈 PERCENTAGES:")
    print(f"   Coverage: {coverage:.2f}% (DB URLs in progress)")
    print(f"   Efficiency: {efficiency:.2f}% (Progress URLs in DB)")
    print(f"   Missing rate: {(missing/total_db*100):.2f}%" if total_db > 0 else "   Missing rate: 0.00%")
    print(f"   Extra rate: {(extra/total_progress*100):.2f}%" if total_progress > 0 else "   Extra rate: 0.00%")
    print()
    
    # Quality assessment
    if coverage >= 99.5 and efficiency >= 99.5:
        quality = "EXCELLENT"
        color = "✅"
    elif coverage >= 95 and efficiency >= 95:
        quality = "GOOD"
        color = "⚠️"
    elif coverage >= 80 and efficiency >= 80:
        quality = "MODERATE"
        color = "⚠️"
    else:
        quality = "POOR"
        color = "❌"
    
    print(f"{color} QUALITY ASSESSMENT: {quality}")
    print()
    
    # Recommendations
    print(f"💡 RECOMMENDATIONS:")
    if missing > 0:
        print(f"   - Sync {missing:,} missing URLs to progress")
    if extra > 0:
        print(f"   - Review {extra:,} extra URLs in progress")
    if coverage < 95:
        print(f"   - Improve coverage (currently {coverage:.1f}%)")
    if efficiency < 95:
        print(f"   - Clean up progress file (efficiency {efficiency:.1f}%)")
    if missing == 0 and extra == 0:
        print(f"   - Coverage is perfect! No action needed")
    print()

def analyze_url_patterns(urls):
    """Analyze URL patterns to identify common structures"""
    patterns = set()
    for url in urls:
        try:
            parsed = urlparse(url)
            # Create pattern based on path structure
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) > 0:
                # Create pattern like: /section/subsection/
                pattern = '/' + '/'.join(path_parts[:2]) + '/'
                patterns.add(pattern)
        except:
            continue
    return patterns

def get_depth_distribution(urls):
    """Get distribution of URLs by depth"""
    depth_dist = defaultdict(int)
    for url in urls:
        try:
            parsed = urlparse(url)
            depth = len([p for p in parsed.path.split('/') if p])
            depth_dist[depth] += 1
        except:
            continue
    return dict(depth_dist)

def group_urls_by_pattern(urls):
    """Group URLs by their path pattern"""
    patterns = defaultdict(set)
    for url in urls:
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) > 0:
                pattern = '/' + '/'.join(path_parts[:2]) + '/'
                patterns[pattern].add(url)
        except:
            continue
    return dict(patterns)

def show_help():
    """Show help information"""
    print("Crawl Coverage Analyzer")
    print("======================")
    print()
    print("Commands:")
    print("  analyze <domain>              Full coverage analysis")
    print("  compare <domain>              Compare progress vs database")
    print("  missing <domain>              Show missing URLs")
    print("  stats <domain>                Coverage statistics")
    print("  help                          Show this help message")
    print()
    print("Examples:")
    print("  python crawl_coverage_analyzer.py analyze cylaw.org")
    print("  python crawl_coverage_analyzer.py compare eur-lex.europa.eu")
    print("  python crawl_coverage_analyzer.py missing cylaw.org")
    print("  python crawl_coverage_analyzer.py stats cylaw.org")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "analyze":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python crawl_coverage_analyzer.py analyze cylaw.org")
            return
        domain = sys.argv[2]
        analyze_coverage(domain)
    elif command == "compare":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python crawl_coverage_analyzer.py compare cylaw.org")
            return
        domain = sys.argv[2]
        compare_progress_vs_database(domain)
    elif command == "missing":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python crawl_coverage_analyzer.py missing cylaw.org")
            return
        domain = sys.argv[2]
        show_missing_urls(domain)
    elif command == "stats":
        if len(sys.argv) < 3:
            print("Error: Please specify domain")
            print("Example: python crawl_coverage_analyzer.py stats cylaw.org")
            return
        domain = sys.argv[2]
        show_coverage_stats(domain)
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        print()
        show_help()

if __name__ == "__main__":
    main() 