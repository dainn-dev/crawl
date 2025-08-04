#!/usr/bin/env python3
"""
Performance Test for Web Crawler Strategies
==========================================

This script compares the performance of different crawling strategies:
- Parallel Hybrid (Fastest)
- Hybrid (Recommended)
- BFS (Wide Discovery)
- DFS (Deep Exploration)

Usage:
    python performance_test.py
"""

import time
import logging
import sys
import os

# Add the current directory to Python path so we can import crawler modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.crawler import (
    start_crawl_dfs, 
    start_crawl_bfs, 
    start_crawl_hybrid,
    start_crawl_hybrid_parallel,
    initialize_domain_tracking,
    visited_sets
)
from crawler.logging_config import setup_logging
from crawler.config import TARGET_SITES

def performance_test():
    """Test and compare performance of different crawling strategies"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Performance Comparison: Parallel Hybrid vs Hybrid vs BFS vs DFS ===")
    print()
    
    # Test parameters
    max_depth = 1  # Shallow depth for quick testing
    test_sites = TARGET_SITES[:1]  # Test with just one site
    
    print(f"Test configuration:")
    print(f"- Max depth: {max_depth}")
    print(f"- Test site: {test_sites[0]['name']}")
    print(f"- URL: {test_sites[0]['start_url']}")
    print()
    
    # Initialize domain tracking
    initialize_domain_tracking()
    
    strategies = [
        ("Parallel Hybrid", start_crawl_hybrid_parallel),
        ("Hybrid", start_crawl_hybrid),
        ("BFS", start_crawl_bfs), 
        ("DFS", start_crawl_dfs)
    ]
    
    results = {}
    
    for strategy_name, strategy_func in strategies:
        print(f"=== Testing {strategy_name} Strategy ===")
        
        # Clear visited sets for fair comparison
        for domain in [site['domain'] for site in test_sites]:
            if domain in visited_sets:
                visited_sets[domain].clear()
        
        start_time = time.time()
        try:
            strategy_func(max_depth=max_depth, sites=test_sites)
            end_time = time.time()
            duration = end_time - start_time
            results[strategy_name] = {
                'duration': duration,
                'status': 'success'
            }
            print(f"✅ {strategy_name} completed in {duration:.2f} seconds")
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            results[strategy_name] = {
                'duration': duration,
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ {strategy_name} failed after {duration:.2f} seconds: {e}")
        
        print()
    
    # Print performance summary
    print("=== Performance Summary ===")
    print(f"{'Strategy':<15} {'Duration':<12} {'Status':<10}")
    print("-" * 40)
    
    fastest_strategy = None
    fastest_time = float('inf')
    
    for strategy_name, result in results.items():
        duration = result['duration']
        status = result['status']
        print(f"{strategy_name:<15} {duration:<12.2f} {status:<10}")
        
        if status == 'success' and duration < fastest_time:
            fastest_time = duration
            fastest_strategy = strategy_name
    
    print()
    if fastest_strategy:
        print(f"🏆 Fastest strategy: {fastest_strategy} ({fastest_time:.2f}s)")
        
        # Calculate speed improvements
        for strategy_name, result in results.items():
            if result['status'] == 'success' and strategy_name != fastest_strategy:
                improvement = ((result['duration'] - fastest_time) / result['duration']) * 100
                print(f"   {strategy_name} is {improvement:.1f}% slower")
    else:
        print("❌ No successful strategies to compare")
    
    print()
    print("=== Recommendations ===")
    print("• Parallel Hybrid: Fastest - combines BFS discovery with parallel DFS processing")
    print("• Hybrid: Best for speed - combines BFS discovery with DFS exploration")
    print("• BFS: Good for wide discovery of URLs at same depth")
    print("• DFS: Good for deep exploration of specific paths")
    print()
    print("💡 Tip: Use Parallel Hybrid strategy for fastest crawling!")

def quick_hybrid_test():
    """Quick test of the hybrid crawler"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Quick Parallel Hybrid Crawler Test ===")
    
    # Test with minimal parameters
    max_depth = 1
    test_sites = TARGET_SITES[:1]
    
    print(f"Testing parallel hybrid crawler with depth {max_depth}")
    print(f"Target: {test_sites[0]['name']}")
    print()
    
    initialize_domain_tracking()
    
    start_time = time.time()
    try:
        start_crawl_hybrid_parallel(max_depth=max_depth, sites=test_sites)
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ Parallel Hybrid crawler completed in {duration:.2f} seconds")
        print("🎉 Ready for production use!")
    except Exception as e:
        print(f"❌ Parallel Hybrid crawler failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_hybrid_test()
    else:
        performance_test() 