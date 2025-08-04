#!/usr/bin/env python3
"""
Fast Web Crawler - Hybrid DFS/BFS Implementation
================================================

This script demonstrates how to use the optimized hybrid crawler
that combines BFS and DFS for faster web crawling.

Usage:
    python run_fast_crawler.py
"""

from crawler.main import run_hybrid_crawl, run_bfs_crawl, run_dfs_crawl, run_hybrid_parallel_crawl
from crawler.config import TARGET_SITES

def main():
    """Run the fast hybrid crawler"""
    print("🚀 Fast Web Crawler - Hybrid DFS/BFS Implementation")
    print("=" * 55)
    print()
    
    # Configuration
    max_depth = 20  # Adjust based on your needs
    sites = TARGET_SITES[:2]  # Start with first 2 sites
    
    print(f"Configuration:")
    print(f"  • Max depth: {max_depth}")
    print(f"  • Target sites: {[site['name'] for site in sites]}")
    print(f"  • Strategy: Parallel Hybrid (BFS + DFS + URL-level parallelism)")
    print()
    
    print("Starting enhanced parallel hybrid crawl...")
    print("This approach uses BFS for initial discovery, then DFS with parallel URL processing.")
    print()
    
    try:
        # Run the enhanced parallel hybrid crawler (fastest approach)
        run_hybrid_parallel_crawl(max_depth=max_depth, sites=sites)
        
        print()
        print("✅ Crawling completed successfully!")
        print("🎉 The parallel hybrid approach should be significantly faster than regular hybrid, DFS, or BFS.")
        
    except Exception as e:
        print(f"❌ Error during crawling: {e}")
        print("Try reducing max_depth or checking your internet connection.")

def compare_strategies():
    """Compare different crawling strategies"""
    print("🔄 Comparing Crawling Strategies")
    print("=" * 40)
    print()
    
    max_depth = 1  # Shallow depth for quick comparison
    sites = TARGET_SITES[:1]  # Just one site for testing
    
    strategies = [
        ("Parallel Hybrid (Fastest)", run_hybrid_parallel_crawl),
        ("Hybrid (Recommended)", run_hybrid_crawl),
        ("BFS (Wide Discovery)", run_bfs_crawl),
        ("DFS (Deep Exploration)", run_dfs_crawl)
    ]
    
    for name, strategy_func in strategies:
        print(f"Testing {name}...")
        try:
            strategy_func(max_depth=max_depth, sites=sites)
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare_strategies()
    else:
        main() 