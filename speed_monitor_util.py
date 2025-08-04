#!/usr/bin/env python3
"""
Speed Monitor Utility
====================

This script provides real-time crawling speed statistics and monitoring.

Usage:
    python speed_monitor_util.py status          # Show current speed stats
    python speed_monitor_util.py report          # Show detailed report
    python speed_monitor_util.py eta <target>    # Show ETA for target URLs
    python speed_monitor_util.py watch           # Continuous monitoring
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.speed_monitor import get_speed_monitor

def show_status():
    """Show current speed status"""
    speed_monitor = get_speed_monitor()
    stats = speed_monitor.get_speed_stats(1)  # Last hour
    
    print("\n" + "="*50)
    print("CRAWLING SPEED STATUS")
    print("="*50)
    print(f"⏱️  Elapsed time: {stats['elapsed_hours']:.2f} hours")
    print(f"📊 Total URLs: {stats['total_urls']:,}")
    print(f"✅ Success rate: {stats['success_rate']:.1f}%")
    print(f"⚡ URLs/hour (last hour): {stats['urls_per_hour']:.1f}")
    print(f"⚡ Overall URLs/hour: {stats['overall_urls_per_hour']:.1f}")
    print(f"⏱️  Avg response time: {stats['avg_response_time']:.2f}s")
    print("="*50)

def show_detailed_report():
    """Show detailed speed report"""
    speed_monitor = get_speed_monitor()
    speed_monitor.print_speed_report(1)  # Last hour

def show_eta(target_urls):
    """Show ETA for target URLs"""
    speed_monitor = get_speed_monitor()
    eta_info = speed_monitor.get_eta(target_urls, 1)  # Based on last hour
    
    if isinstance(eta_info, str):
        print(f"\nETA: {eta_info}")
    else:
        print("\n" + "="*50)
        print("ESTIMATED COMPLETION TIME")
        print("="*50)
        print(f"🎯 Target URLs: {target_urls:,}")
        print(f"📊 Current URLs: {eta_info['remaining_urls'] + speed_monitor.total_urls:,}")
        print(f"📈 URLs/hour: {eta_info['urls_per_hour']:.1f}")
        print(f"⏰ Hours needed: {eta_info['hours_needed']:.1f}")
        print(f"📅 ETA: {eta_info['eta_datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

def watch_mode():
    """Continuous monitoring mode"""
    speed_monitor = get_speed_monitor()
    
    print("\n🔄 Starting continuous monitoring... (Press Ctrl+C to stop)")
    print("="*60)
    
    try:
        while True:
            stats = speed_monitor.get_speed_stats(1)  # Last hour
            
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")
            
            print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            print(f"📊 Total URLs: {stats['total_urls']:,}")
            print(f"⚡ URLs/hour: {stats['urls_per_hour']:.1f}")
            print(f"✅ Success rate: {stats['success_rate']:.1f}%")
            print(f"⏱️  Avg response: {stats['avg_response_time']:.2f}s")
            print(f"⏰ Elapsed: {stats['elapsed_hours']:.2f}h")
            print("="*60)
            
            # Show domain stats if available
            domain_stats = speed_monitor.get_domain_stats()
            if domain_stats:
                print("🌐 DOMAIN STATS:")
                for domain, data in sorted(domain_stats.items(), 
                                         key=lambda x: x[1]['total'], reverse=True)[:3]:
                    success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                    print(f"   {domain}: {data['total']:,} URLs ({success_rate:.1f}% success)")
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped.")

def show_help():
    """Show help information"""
    print("Speed Monitor Utility")
    print("====================")
    print()
    print("Commands:")
    print("  status                    Show current speed status")
    print("  report                    Show detailed speed report")
    print("  eta <target>              Show ETA for target URLs")
    print("  watch                     Continuous monitoring")
    print("  help                      Show this help message")
    print()
    print("Examples:")
    print("  python speed_monitor_util.py status")
    print("  python speed_monitor_util.py report")
    print("  python speed_monitor_util.py eta 10000")
    print("  python speed_monitor_util.py watch")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "report":
        show_detailed_report()
    elif command == "eta":
        if len(sys.argv) < 3:
            print("Error: Please specify target number of URLs")
            print("Example: python speed_monitor_util.py eta 10000")
            return
        try:
            target_urls = int(sys.argv[2])
            show_eta(target_urls)
        except ValueError:
            print("Error: Target URLs must be a number")
    elif command == "watch":
        watch_mode()
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        print()
        show_help()

if __name__ == "__main__":
    main() 