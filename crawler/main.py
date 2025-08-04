import logging
from .crawler import (
    start_crawl_dfs, 
    start_crawl_bfs, 
    start_crawl_hybrid,
    start_crawl_hybrid_parallel,
    crawl_page_hybrid_manual_control,
    trigger_phase2_dfs,
    initialize_domain_tracking,
    get_progress_summary,
    clear_progress
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

def run_resume_crawl(max_depth=3, sites=None):
    """Resume crawling from saved progress"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES
    
    # Show current progress
    summary = get_progress_summary()
    if summary:
        logger.info("Found saved progress:")
        for domain, data in summary.items():
            logger.info(f"  {domain}: {data['urls_crawled']} URLs at depth {data['current_depth']}")
    else:
        logger.info("No saved progress found. Starting fresh crawl.")
    
    logger.info(f"Resuming parallel hybrid crawl with depth {max_depth}")
    start_crawl_hybrid_parallel(max_depth=max_depth, sites=sites)
    logger.info("Resume crawl completed!")

def run_manual_phase_crawl(max_depth=3, sites=None, bfs_depth=1):
    """Run hybrid crawl with manual phase control"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if sites is None:
        sites = TARGET_SITES[:1]  # Start with one site for manual control
    
    logger.info(f"Starting manual phase control crawl with depth {max_depth}")
    logger.info(f"Phase 1 will crawl up to depth {bfs_depth}")
    
    for site in sites:
        domain = site['domain']
        start_url = site['start_url']
        site_name = site['name']
        
        logger.info(f"Starting manual phase control for {site_name} ({domain})")
        
        try:
            # Phase 1: Automatic BFS
            phase1_result = crawl_page_hybrid_manual_control(
                start_url=start_url,
                domain=domain,
                max_depth=max_depth,
                bfs_depth=bfs_depth,
                exclude_extensions=site.get('exclude_extensions', []),
                max_workers=5,
                save_interval=25
            )
            
            logger.info(f"Phase 1 completed: {phase1_result['urls_processed']} URLs processed")
            logger.info(f"Phase 1 discovered: {phase1_result['phase1_urls']} URLs")
            
            # Phase 2: Manual DFS trigger
            logger.info("Phase 2 ready to start. Use trigger_phase2_dfs() to continue.")
            
            return phase1_result
            
        except Exception as e:
            logger.error(f"Manual phase control failed: {e}")
            return None

if __name__ == "__main__":
    main()