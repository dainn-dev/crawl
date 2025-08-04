#!/usr/bin/env python3
"""
Manual Phase Control Crawler
===========================

This script demonstrates how to manually control the hybrid crawler phases.
Phase 1: BFS for initial discovery (automatic)
Phase 2: DFS for deeper exploration (manual trigger)

Usage:
    python manual_phase_crawler.py
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.crawler import crawl_page_hybrid_manual_control, trigger_phase2_dfs
from crawler.logging_config import setup_logging
from crawler.config import TARGET_SITES

def main():
    """Demonstrate manual phase control"""
    setup_logging()
    
    print("=== Manual Phase Control Hybrid Crawler ===")
    print()
    
    # Configuration
    max_depth = 3
    bfs_depth = 1  # Phase 1 will crawl up to depth 1
    test_sites = TARGET_SITES[:1]  # Test with one site
    
    for site in test_sites:
        domain = site['domain']
        start_url = site['start_url']
        site_name = site['name']
        
        print(f"Target: {site_name} ({domain})")
        print(f"Start URL: {start_url}")
        print(f"Max depth: {max_depth}")
        print(f"Phase 1 depth: {bfs_depth}")
        print()
        
        # Phase 1: Automatic BFS
        print("🚀 Starting Phase 1 (BFS) - Automatic...")
        print("Phase 1 will discover URLs using BFS strategy")
        print()
        
        try:
            phase1_result = crawl_page_hybrid_manual_control(
                start_url=start_url,
                domain=domain,
                max_depth=max_depth,
                bfs_depth=bfs_depth,
                exclude_extensions=site.get('exclude_extensions', []),
                max_workers=5,
                save_interval=25
            )
            
            print("✅ Phase 1 completed successfully!")
            print(f"   URLs processed: {phase1_result['urls_processed']}")
            print(f"   Phase 1 URLs discovered: {phase1_result['phase1_urls']}")
            print()
            
            # Ask user if they want to continue to Phase 2
            print("Phase 2 (DFS) is ready to start.")
            print("Phase 2 will explore deeper levels using DFS strategy.")
            print()
            
            while True:
                response = input("Do you want to start Phase 2? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    print()
                    print("🚀 Starting Phase 2 (DFS) - Manual trigger...")
                    print("Phase 2 will explore deeper levels using DFS strategy")
                    print()
                    
                    try:
                        phase2_result = trigger_phase2_dfs(
                            phase1_result=phase1_result,
                            max_workers=5,
                            save_interval=25
                        )
                        
                        print("✅ Phase 2 completed successfully!")
                        print(f"   Total URLs processed: {phase2_result['total_urls_processed']}")
                        print(f"   Final depth reached: {phase2_result['final_depth']}")
                        print()
                        print("🎉 Manual phase control crawl completed!")
                        
                    except Exception as e:
                        print(f"❌ Phase 2 failed: {e}")
                    
                    break
                    
                elif response in ['n', 'no']:
                    print()
                    print("⏸️  Phase 2 skipped. Crawl completed after Phase 1.")
                    print("You can resume Phase 2 later using the resume functionality.")
                    break
                    
                else:
                    print("Please enter 'y' or 'n'")
            
        except Exception as e:
            print(f"❌ Phase 1 failed: {e}")

def phase1_only():
    """Run only Phase 1 for testing"""
    setup_logging()
    
    print("=== Phase 1 Only Test ===")
    print()
    
    max_depth = 3
    bfs_depth = 1
    test_sites = TARGET_SITES[:1]
    
    for site in test_sites:
        domain = site['domain']
        start_url = site['start_url']
        site_name = site['name']
        
        print(f"Testing Phase 1 for: {site_name} ({domain})")
        print()
        
        try:
            phase1_result = crawl_page_hybrid_manual_control(
                start_url=start_url,
                domain=domain,
                max_depth=max_depth,
                bfs_depth=bfs_depth,
                exclude_extensions=site.get('exclude_extensions', []),
                max_workers=3,
                save_interval=10
            )
            
            print("✅ Phase 1 test completed!")
            print(f"   URLs processed: {phase1_result['urls_processed']}")
            print(f"   Phase 1 URLs discovered: {phase1_result['phase1_urls']}")
            
        except Exception as e:
            print(f"❌ Phase 1 test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "phase1":
        phase1_only()
    else:
        main() 