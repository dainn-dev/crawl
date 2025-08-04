import logging
from .crawler import (
    start_crawl_dfs, 
    start_crawl_bfs, 
    start_crawl_hybrid,
    start_crawl_hybrid_parallel,
    initialize_domain_tracking
)
from .logging_config import setup_logging
from .config import TARGET_SITES

def main():
    """Main function to run the crawler with different strategies"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Web Crawler with Multiple Strategies ===")
    print("Available crawling strategies:")
    print("1. DFS (Depth-First Search) - Good for deep exploration")
    print("2. BFS (Breadth-First Search) - Good for wide discovery")
    print("3. Hybrid (BFS + DFS) - Best of both worlds for speed")
    print()
    
    # Initialize domain tracking
    initialize_domain_tracking()
    
    # Example usage with different strategies
    max_depth = 3  # Adjust based on your needs
    sites = TARGET_SITES[:2]  # Start with first 2 sites for testing
    
    print(f"Target sites: {[site['name'] for site in sites]}")
    print(f"Max depth: {max_depth}")
    print()
    
    # Strategy 1: Hybrid (Recommended for speed)
    print("=== Starting Hybrid Crawl (Recommended) ===")
    try:
        start_crawl_hybrid(max_depth=max_depth, sites=sites)
        print("✅ Hybrid crawl completed successfully!")
    except Exception as e:
        print(f"❌ Hybrid crawl failed: {e}")
    
    print()
    
    # Strategy 2: BFS (Good for wide discovery)
    print("=== Starting BFS Crawl ===")
    try:
        start_crawl_bfs(max_depth=max_depth, sites=sites)
        print("✅ BFS crawl completed successfully!")
    except Exception as e:
        print(f"❌ BFS crawl failed: {e}")
    
    print()
    
    # Strategy 3: DFS (Good for deep exploration)
    print("=== Starting DFS Crawl ===")
    try:
        start_crawl_dfs(max_depth=max_depth, sites=sites)
        print("✅ DFS crawl completed successfully!")
    except Exception as e:
        print(f"❌ DFS crawl failed: {e}")

def run_hybrid_crawl(max_depth=3, sites=None):
    """Run only the hybrid crawler (fastest approach)"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES
    
    logger.info(f"Starting fast hybrid crawl with depth {max_depth}")
    start_crawl_hybrid(max_depth=max_depth, sites=sites)
    logger.info("Hybrid crawl completed!")

def run_bfs_crawl(max_depth=3, sites=None):
    """Run only the BFS crawler (good for wide discovery)"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES
    
    logger.info(f"Starting BFS crawl with depth {max_depth}")
    start_crawl_bfs(max_depth=max_depth, sites=sites)
    logger.info("BFS crawl completed!")

def run_dfs_crawl(max_depth=3, sites=None):
    """Run only the DFS crawler (good for deep exploration)"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES
    
    logger.info(f"Starting DFS crawl with depth {max_depth}")
    start_crawl_dfs(max_depth=max_depth, sites=sites)
    logger.info("DFS crawl completed!")

def run_hybrid_parallel_crawl(max_depth=3, sites=None):
    """Run the enhanced parallel hybrid crawler (fastest approach with URL-level parallelism)"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES
    
    logger.info(f"Starting enhanced parallel hybrid crawl with depth {max_depth}")
    start_crawl_hybrid_parallel(max_depth=max_depth, sites=sites)
    logger.info("Parallel hybrid crawl completed!")

if __name__ == "__main__":
    main()