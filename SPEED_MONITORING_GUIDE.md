# Speed Monitoring Guide

## Overview

The crawler now includes comprehensive speed monitoring that tracks URLs per hour, response times, success rates, and provides real-time statistics.

## Speed Monitoring Features

### 📊 **Real-time Statistics**
- **URLs per hour** (last hour and overall)
- **Success rate** percentage
- **Average response time** per URL
- **Domain-specific statistics**
- **Status code distribution**

### ⏱️ **Time Tracking**
- **Elapsed time** in hours
- **ETA calculations** for target URLs
- **Continuous monitoring** with live updates

### 🎯 **Performance Metrics**
- **Response time tracking** per domain
- **Error rate monitoring**
- **Parallel processing efficiency**

## How to Check Speed

### 1. **Real-time Status**
```bash
python speed_monitor_util.py status
```
Shows current speed statistics including URLs/hour, success rate, and elapsed time.

### 2. **Detailed Report**
```bash
python speed_monitor_util.py report
```
Provides comprehensive report with domain statistics and status code breakdown.

### 3. **ETA Calculation**
```bash
python speed_monitor_util.py eta 10000
```
Shows estimated completion time for a target number of URLs.

### 4. **Continuous Monitoring**
```bash
python speed_monitor_util.py watch
```
Real-time monitoring that updates every 5 seconds (press Ctrl+C to stop).

## Speed Metrics Explained

### **URLs per Hour**
- **Last Hour**: Speed based on the most recent hour of crawling
- **Overall**: Average speed since crawling started
- **Formula**: `URLs processed / hours elapsed`

### **Success Rate**
- Percentage of URLs that returned HTTP 200 status
- **Formula**: `(Successful URLs / Total URLs) × 100`

### **Response Time**
- Average time to fetch and process each URL
- Includes network time, parsing time, and database operations

### **Domain Performance**
- Per-domain statistics showing which sites are fastest/slowest
- Helps identify performance bottlenecks

## Example Output

```
==================================================
CRAWLING SPEED STATUS
==================================================
⏱️  Elapsed time: 2.45 hours
📊 Total URLs: 1,234
✅ Success rate: 95.2%
⚡ URLs/hour (last hour): 156.7
⚡ Overall URLs/hour: 503.7
⏱️  Avg response time: 1.23s
==================================================
```

## Performance Optimization Tips

### **High URLs/Hour** (>500/hour)
- ✅ Good performance
- Consider increasing max_depth for more thorough crawling
- May want to add more target sites

### **Medium URLs/Hour** (100-500/hour)
- ⚠️ Moderate performance
- Check for network issues or slow target sites
- Consider adjusting CRAWL_DELAY in config

### **Low URLs/Hour** (<100/hour)
- ❌ Poor performance
- Check internet connection
- Verify target sites are accessible
- Consider reducing max_depth temporarily

## Monitoring During Crawling

### **Automatic Speed Reports**
The crawler automatically prints speed updates every 5 minutes:
```
2025-08-04 15:45:23,456 [INFO] Speed Update: 156.7 URLs/hour | Total: 1,234 | Success Rate: 95.2%
```

### **Final Speed Report**
When crawling completes, a detailed report is automatically shown:
```
============================================================
CRAWLING SPEED REPORT
============================================================
📊 OVERALL STATISTICS:
   Total URLs crawled: 1,234
   Successful: 1,174 (95.2%)
   Failed: 60
   Elapsed time: 2.45 hours

⚡ SPEED STATISTICS (last 1 hour):
   URLs per hour: 156.7
   URLs in window: 157
   Overall URLs/hour: 503.7
   Average response time: 1.23s

🌐 DOMAIN STATISTICS:
   cylaw.org:
     Total: 789 | Success: 750 (95.1%)
     Avg response time: 0.89s
   eur-lex.europa.eu:
     Total: 445 | Success: 424 (95.3%)
     Avg response time: 1.67s

📋 STATUS CODE STATISTICS:
   200: 1,174 (95.2%)
   404: 45 (3.6%)
   500: 15 (1.2%)
============================================================
```

## Troubleshooting

### **No Speed Data**
If you see 0 URLs/hour:
1. Make sure crawling has started
2. Check that speed monitoring is enabled
3. Wait for the first URLs to be processed

### **Inaccurate ETA**
- ETA is based on recent speed (last hour)
- If speed varies significantly, ETA may be inaccurate
- Use `watch` mode to monitor real-time changes

### **Performance Issues**
- Check network connectivity
- Verify target sites are responding
- Consider adjusting CRAWL_DELAY in config
- Monitor for rate limiting from target sites

## Advanced Usage

### **Custom Time Windows**
You can modify the speed monitor to use different time windows:
```python
# In speed_monitor_util.py, change the hours parameter:
stats = speed_monitor.get_speed_stats(2)  # Last 2 hours instead of 1
```

### **Export Speed Data**
Add this to your scripts to export speed data:
```python
from crawler.speed_monitor import get_speed_monitor
import json

speed_monitor = get_speed_monitor()
stats = speed_monitor.get_speed_stats(1)

with open('speed_data.json', 'w') as f:
    json.dump(stats, f, indent=2)
```

## Integration with Existing Tools

### **Database Cleanup + Speed Monitoring**
```bash
# Check database status and speed
python db_cleanup.py status
python speed_monitor_util.py status
```

### **Resume Crawling + Speed Monitoring**
```bash
# Resume crawling and monitor speed
python resume_crawler.py resume &
python speed_monitor_util.py watch
```

This comprehensive speed monitoring system helps you track crawling performance in real-time and optimize your crawling strategy based on actual performance metrics. 