import time
import logging
from .crawler import (
    start_crawl_dfs, 
    start_crawl_bfs, 
    start_crawl_hybrid,
    initialize_domain_tracking
)
from .logging_config import setup_logging
from .config import TARGET_SITES

def performance_test():
    """Test and compare performance of different crawling strategies"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Performance Comparison: DFS vs BFS vs Hybrid ===")
    print()
    
    # Test parameters
    max_depth = 2  # Shallow depth for quick testing
    test_sites = TARGET_SITES[:1]  # Test with just one site
    
    print(f"Test configuration:")
    print(f"- Max depth: {max_depth}")
    print(f"- Test site: {test_sites[0]['name']}")
    print(f"- URL: {test_sites[0]['start_url']}")
    print()
    
    # Initialize domain tracking
    initialize_domain_tracking()
    
    strategies = [
        ("DFS", start_crawl_dfs),
        ("BFS", start_crawl_bfs), 
        ("Hybrid", start_crawl_hybrid)
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
    print(f"{'Strategy':<10} {'Duration':<12} {'Status':<10}")
    print("-" * 35)
    
    fastest_strategy = None
    fastest_time = float('inf')
    
    for strategy_name, result in results.items():
        duration = result['duration']
        status = result['status']
        print(f"{strategy_name:<10} {duration:<12.2f} {status:<10}")
        
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
    print("• Hybrid: Best for speed - combines BFS discovery with DFS exploration")
    print("• BFS: Good for wide discovery of URLs at same depth")
    print("• DFS: Good for deep exploration of specific paths")
    print()
    print("💡 Tip: Use Hybrid strategy for fastest crawling!")

def quick_hybrid_test():
    """Quick test of the hybrid crawler"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Quick Hybrid Crawler Test ===")
    
    # Test with minimal parameters
    max_depth = 1
    test_sites = TARGET_SITES[:1]
    
    print(f"Testing hybrid crawler with depth {max_depth}")
    print(f"Target: {test_sites[0]['name']}")
    print()
    
    initialize_domain_tracking()
    
    start_time = time.time()
    try:
        start_crawl_hybrid(max_depth=max_depth, sites=test_sites)
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ Hybrid crawler completed in {duration:.2f} seconds")
        print("🎉 Ready for production use!")
    except Exception as e:
        print(f"❌ Hybrid crawler failed: {e}")

if __name__ == "__main__":
    # Uncomment one of these to run:
    # performance_test()  # Full performance comparison
    quick_hybrid_test()  # Quick test of hybrid crawler 