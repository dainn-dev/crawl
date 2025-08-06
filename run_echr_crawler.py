#!/usr/bin/env python3
"""
ECHR Crawler Runner Script

This script provides an easy way to run the ECHR crawler with different configurations.
"""

import argparse
import logging
from echr.echr_crawler import ECHRCrawler
from crawler.logging_config import setup_logging

def main():
    """Main function to run the ECHR crawler with command line arguments"""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ECHR Crawler')
    parser.add_argument('--url', 
                       default="https://hudoc.echr.coe.int/#{%22tabview%22:[%22document%22]}",
                       help='Starting URL for crawling')
    parser.add_argument('--headless', 
                       action='store_true', 
                       default=True,
                       help='Run browser in headless mode')
    parser.add_argument('--method', 
                       choices=['bfs', 'dfs'], 
                       default='dfs',
                       help='Crawling method (BFS or DFS)')
    parser.add_argument('--max-depth', 
                       type=int, 
                       default=3,
                       help='Maximum crawl depth')
    parser.add_argument('--max-urls', 
                       type=int, 
                       default=100,
                       help='Maximum URLs to crawl (for DFS)')
    parser.add_argument('--max-urls-per-depth', 
                       type=int, 
                       default=50,
                       help='Maximum URLs per depth level (for BFS)')
    parser.add_argument('--scroll-pause', 
                       type=int, 
                       default=2,
                       help='Time to wait between scrolls')
    parser.add_argument('--max-scrolls', 
                       type=int, 
                       default=10,
                       help='Maximum scroll attempts per page')
    
    args = parser.parse_args()
    
    # Create crawler instance
    crawler = ECHRCrawler(
        headless=args.headless,
        scroll_pause_time=args.scroll_pause,
        max_scroll_attempts=args.max_scrolls
    )
    
    try:
        # Setup WebDriver
        logger.info("Setting up Chrome WebDriver...")
        crawler.setup_driver()
        
        # Start crawling based on method
        logger.info(f"Starting ECHR crawler with {args.method.upper()} method...")
        logger.info(f"Target URL: {args.url}")
        logger.info(f"Max depth: {args.max_depth}")
        
        if args.method == 'bfs':
            logger.info(f"Max URLs per depth: {args.max_urls_per_depth}")
            crawler.crawl_site_bfs(
                start_url=args.url,
                max_depth=args.max_depth,
                max_urls_per_depth=args.max_urls_per_depth
            )
        else:  # dfs
            logger.info(f"Max URLs: {args.max_urls}")
            crawler.crawl_site_dfs(
                start_url=args.url,
                max_depth=args.max_depth,
                max_urls=args.max_urls
            )
        
        logger.info("Crawling completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
    finally:
        crawler.close()
        logger.info("Crawler closed")

if __name__ == "__main__":
    main() 