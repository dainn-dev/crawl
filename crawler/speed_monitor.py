#!/usr/bin/env python3
"""
Speed Monitor for Web Crawler
=============================

This module tracks crawling speed and provides real-time statistics
including URLs per hour, average response times, and performance metrics.
"""

import time
import threading
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class SpeedMonitor:
    def __init__(self, window_size=3600):  # 1 hour window by default
        self.start_time = time.time()
        self.total_urls = 0
        self.successful_urls = 0
        self.failed_urls = 0
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.url_timestamps = deque(maxlen=10000)  # Keep last 10000 URL timestamps
        self.lock = threading.Lock()
        
        # Performance tracking
        self.domain_stats = {}
        self.status_codes = {}
        
    def record_url(self, url, domain, status_code, response_time=None, success=True):
        """Record a crawled URL with timing information"""
        with self.lock:
            current_time = time.time()
            self.total_urls += 1
            
            if success:
                self.successful_urls += 1
            else:
                self.failed_urls += 1
            
            # Record timestamp for speed calculation
            self.url_timestamps.append(current_time)
            
            # Record response time if provided
            if response_time is not None:
                self.response_times.append(response_time)
            
            # Track domain statistics
            if domain not in self.domain_stats:
                self.domain_stats[domain] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'avg_response_time': 0,
                    'response_times': deque(maxlen=100)
                }
            
            self.domain_stats[domain]['total'] += 1
            if success:
                self.domain_stats[domain]['successful'] += 1
            else:
                self.domain_stats[domain]['failed'] += 1
            
            if response_time is not None:
                self.domain_stats[domain]['response_times'].append(response_time)
                # Update average response time for this domain
                times = list(self.domain_stats[domain]['response_times'])
                self.domain_stats[domain]['avg_response_time'] = sum(times) / len(times)
            
            # Track status codes
            if status_code not in self.status_codes:
                self.status_codes[status_code] = 0
            self.status_codes[status_code] += 1
    
    def get_speed_stats(self, hours=1):
        """Get speed statistics for the specified time window"""
        with self.lock:
            current_time = time.time()
            window_start = current_time - (hours * 3600)
            
            # Count URLs in the time window
            urls_in_window = sum(1 for timestamp in self.url_timestamps 
                               if timestamp >= window_start)
            
            # Calculate URLs per hour
            urls_per_hour = urls_in_window / hours if hours > 0 else 0
            
            # Calculate overall URLs per hour since start
            elapsed_hours = (current_time - self.start_time) / 3600
            overall_urls_per_hour = self.total_urls / elapsed_hours if elapsed_hours > 0 else 0
            
            # Calculate average response time
            avg_response_time = 0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
            
            return {
                'urls_per_hour': urls_per_hour,
                'overall_urls_per_hour': overall_urls_per_hour,
                'total_urls': self.total_urls,
                'successful_urls': self.successful_urls,
                'failed_urls': self.failed_urls,
                'success_rate': (self.successful_urls / self.total_urls * 100) if self.total_urls > 0 else 0,
                'avg_response_time': avg_response_time,
                'elapsed_hours': elapsed_hours,
                'urls_in_window': urls_in_window
            }
    
    def get_domain_stats(self):
        """Get statistics by domain"""
        with self.lock:
            return self.domain_stats.copy()
    
    def get_status_code_stats(self):
        """Get statistics by status code"""
        with self.lock:
            return self.status_codes.copy()
    
    def print_speed_report(self, hours=1):
        """Print a comprehensive speed report"""
        stats = self.get_speed_stats(hours)
        domain_stats = self.get_domain_stats()
        status_stats = self.get_status_code_stats()
        
        print("\n" + "="*60)
        print("CRAWLING SPEED REPORT")
        print("="*60)
        
        # Overall statistics
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Total URLs crawled: {stats['total_urls']:,}")
        print(f"   Successful: {stats['successful_urls']:,} ({stats['success_rate']:.1f}%)")
        print(f"   Failed: {stats['failed_urls']:,}")
        print(f"   Elapsed time: {stats['elapsed_hours']:.2f} hours")
        print()
        
        # Speed statistics
        print(f"⚡ SPEED STATISTICS (last {hours} hour{'s' if hours != 1 else ''}):")
        print(f"   URLs per hour: {stats['urls_per_hour']:.1f}")
        print(f"   URLs in window: {stats['urls_in_window']:,}")
        print(f"   Overall URLs/hour: {stats['overall_urls_per_hour']:.1f}")
        print(f"   Average response time: {stats['avg_response_time']:.2f}s")
        print()
        
        # Domain statistics
        if domain_stats:
            print(f"🌐 DOMAIN STATISTICS:")
            for domain, data in sorted(domain_stats.items(), 
                                     key=lambda x: x[1]['total'], reverse=True):
                success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                print(f"   {domain}:")
                print(f"     Total: {data['total']:,} | Success: {data['successful']:,} ({success_rate:.1f}%)")
                print(f"     Avg response time: {data['avg_response_time']:.2f}s")
            print()
        
        # Status code statistics
        if status_stats:
            print(f"📋 STATUS CODE STATISTICS:")
            for status_code, count in sorted(status_stats.items()):
                percentage = (count / stats['total_urls'] * 100) if stats['total_urls'] > 0 else 0
                print(f"   {status_code}: {count:,} ({percentage:.1f}%)")
        
        print("="*60)
    
    def get_eta(self, target_urls, hours=1):
        """Estimate time to complete based on current speed"""
        stats = self.get_speed_stats(hours)
        urls_per_hour = stats['urls_per_hour']
        
        if urls_per_hour <= 0:
            return "Unknown (no URLs processed in time window)"
        
        remaining_urls = target_urls - stats['total_urls']
        if remaining_urls <= 0:
            return "Completed"
        
        hours_needed = remaining_urls / urls_per_hour
        eta_time = datetime.now() + timedelta(hours=hours_needed)
        
        return {
            'hours_needed': hours_needed,
            'eta_datetime': eta_time,
            'urls_per_hour': urls_per_hour,
            'remaining_urls': remaining_urls
        }
    
    def log_speed_update(self, interval_minutes=5):
        """Log speed update at regular intervals"""
        stats = self.get_speed_stats(1)  # Last hour
        logger.info(f"Speed Update: {stats['urls_per_hour']:.1f} URLs/hour | "
                   f"Total: {stats['total_urls']:,} | "
                   f"Success Rate: {stats['success_rate']:.1f}%")

# Global speed monitor instance
speed_monitor = SpeedMonitor()

def get_speed_monitor():
    """Get the global speed monitor instance"""
    return speed_monitor 