import argparse
from .db import create_tables
from .crawler import start_crawl, start_crawl_bfs, start_crawl_dfs
from . import config

def main():
    parser = argparse.ArgumentParser(description='Multi-site legal web crawler')
    parser.add_argument('--no-check', action='store_true', 
                       help='Skip checking and updating existing URLs in database')
    parser.add_argument('--max-depth', type=int, default=5,
                       help='Maximum crawl depth (default: 5)')
    parser.add_argument('--threads', type=int, default=5,
                       help='Number of threads for crawling (default: 5)')
    parser.add_argument('--delay', type=float, default=0.01,
                       help='Delay between requests in seconds (default: 0.01)')
    parser.add_argument('--site', type=str, choices=[site['name'] for site in config.TARGET_SITES],
                       help='Name of the target site to crawl (default: all)')
    parser.add_argument('--use-bfs', action='store_true',
                       help='Use Breadth-First Search instead of Depth-First Search')
    args = parser.parse_args()
    
    # Set configuration based on command line arguments
    config.IS_CHECK = not args.no_check
    config.MAX_THREADS = args.threads
    config.CRAWL_DELAY = args.delay

    # Filter target sites if --site is provided
    if args.site:
        selected_sites = [site for site in config.TARGET_SITES if site['name'] == args.site]
    else:
        selected_sites = config.TARGET_SITES

    print("Multi-site Legal Web Crawler starting...")
    print(f"Check existing URLs: {config.IS_CHECK}")
    print(f"Max depth: {args.max_depth}")
    print(f"Number of threads: {config.MAX_THREADS}")
    print(f"Crawl delay: {config.CRAWL_DELAY} seconds")
    print(f"Traversal method: {'BFS' if args.use_bfs else 'DFS'}")
    print(f"Target sites: {[site['name'] for site in selected_sites]}")
    
    create_tables()
    print("Database tables created.")
    
    # Use BFS or DFS based on the argument
    if args.use_bfs:
        start_crawl_bfs(max_depth=args.max_depth, sites=selected_sites)
    else:
        start_crawl_dfs(max_depth=args.max_depth, sites=selected_sites)

if __name__ == "__main__":
    main()